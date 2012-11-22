from unittest import TestCase, TestSuite, makeSuite

from mtj.multimer.buffer import Buffer, TimedBuffer

qSilo = lambda value, full: TimedBuffer(delta=100, period=3600, timestamp=0,
    delta_min=0, delta_factor=1, value=value, full=full)
qLPos = lambda value: TimedBuffer(delta=40, period=3600, timestamp=0,
    delta_min=1, delta_factor=-1, value=value, full=28000)
qLPosS = lambda value: TimedBuffer(delta=30, period=3600, timestamp=0,
    delta_min=1, delta_factor=-1, value=value, full=28000)


class TestBuffer(TestCase):
    """
    Unit tests for buffers.
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_0000_base(self):
        buf = Buffer()
        self.assertEqual(buf.value, 0)

    def test_0001_params(self):
        buf = Buffer(value=50)
        self.assertEqual(buf.value, 50)
        buf = Buffer(full=200)
        self.assertEqual(buf.full, 200)
        buf = Buffer(value=10, empty=10)
        self.assertEqual(buf.empty, 10)

    def test_0010_assertions(self):
        self.assertRaises(AssertionError, Buffer, empty=10)
        self.assertRaises(AssertionError, Buffer, value=10000, full=200)
        self.assertRaises(AssertionError, Buffer, value=-1000, empty=-200)


class TestTimedBuffer(TestCase):

    def setUp(self):
        self.full_silo = qSilo(60000, 60000)
        self.part_silo = qSilo(1234, 60000)
        self.zero_silo = qSilo(0, 60000)

        self.full_pos = qLPos(28000)
        self.part_pos = qLPos(1234)
        self.zero_pos = qLPos(0)

    def tearDown(self):
        pass

    def bufferChecker(self, buff, timestamp, value, alive=None):
        self.assertEqual(buff.getCurrent(timestamp).value, value)
        if alive is not None:
            self.assertEqual(buff.getCurrent(timestamp).alive, alive)

    def test_0010_assertions(self):
        self.assertRaises(AssertionError, TimedBuffer, period=0)
        self.assertRaises(AssertionError, TimedBuffer, delta_min=-1)

    def test_0100_standard_inc(self):
        self.bufferChecker(self.zero_silo, 1, 0)
        self.bufferChecker(self.zero_silo, 3600, 100)
        self.bufferChecker(self.zero_silo, 35999, 900)
        self.bufferChecker(self.zero_silo, 36000, 1000)
        self.bufferChecker(self.zero_silo, 2159999, 59900, True)
        self.bufferChecker(self.zero_silo, 2160000, 60000, True)
        self.bufferChecker(self.zero_silo, 2163600, 60000, False)

    def test_0101_standard_inc(self):
        self.bufferChecker(self.part_silo, 1, 1234)
        self.bufferChecker(self.part_silo, 3600, 1334)
        self.bufferChecker(self.part_silo, 35999, 2134)
        self.bufferChecker(self.part_silo, 36000, 2234)
        self.bufferChecker(self.part_silo, 2113200, 59934)
        self.bufferChecker(self.part_silo, 2116799, 59934, True)
        # This pushed it over the top.
        self.bufferChecker(self.part_silo, 2116800, 60000, False)
        self.bufferChecker(self.part_silo, 2120399, 60000, False)
        self.bufferChecker(self.part_silo, 2120400, 60000, False)
        self.bufferChecker(self.part_silo, 2160000, 60000)

    def test_0102_standard_inc(self):
        self.bufferChecker(self.full_silo, 1, 60000)
        self.bufferChecker(self.full_silo, 3600, 60000)
        self.bufferChecker(self.full_silo, 7201, 60000)

    def test_0200_standard_dec(self):
        self.bufferChecker(self.full_pos, 1, 28000)
        self.bufferChecker(self.full_pos, 3599, 28000)
        self.bufferChecker(self.full_pos, 3600, 27960)
        self.bufferChecker(self.full_pos, 3600, 27960)
        self.bufferChecker(self.full_pos, 252000, 25200)
        self.bufferChecker(self.full_pos, 2519999, 40, True)
        self.bufferChecker(self.full_pos, 2520000, 0, True)
        self.bufferChecker(self.full_pos, 2523599, 0, True)
        self.bufferChecker(self.full_pos, 2523600, 0, False)

    def test_0201_standard_dec(self):
        self.bufferChecker(self.part_pos, 1, 1234)
        self.bufferChecker(self.part_pos, 3600, 1194)
        self.bufferChecker(self.part_pos, 107999, 74, True)
        self.bufferChecker(self.part_pos, 108000, 34, True)
        self.bufferChecker(self.part_pos, 111599, 34, True)
        self.bufferChecker(self.part_pos, 111600, 34, False)

    def test_0202_standard_dec(self):
        self.bufferChecker(self.zero_pos, 1, 0)
        self.bufferChecker(self.zero_pos, 3600, 0)
        self.bufferChecker(self.zero_pos, 36000, 0)

    def test_1000_abnormal_setup(self):
        weird1 = TimedBuffer(delta=40, period=3600, timestamp=0, delta_min=0.325,
            delta_factor=-1, value=140, full=1000)
        self.bufferChecker(weird1, 3600, 100)
        self.bufferChecker(weird1, 7200, 60)
        self.bufferChecker(weird1, 14399, 20)
        self.bufferChecker(weird1, 14400, 7)
        self.bufferChecker(weird1, 22400, 7)

    def test_1001_abnormal_setup(self):
        weird1 = TimedBuffer(delta=100, period=3600, timestamp=0,
            delta_min=(1./3), delta_factor=1, value=115, full=1000)
        self.bufferChecker(weird1, 3600, 215)
        self.bufferChecker(weird1, 7200, 315)
        self.bufferChecker(weird1, 28800, 915)
        self.bufferChecker(weird1, 32400, 981, False)

    def test_1002_abnormal_setup(self):
        weird1 = TimedBuffer(delta=100, period=3600, timestamp=0,
            delta_min=(1./3), delta_factor=-1, value=115, full=1000,
            empty=-180)
        self.bufferChecker(weird1, 3600, 15)
        self.bufferChecker(weird1, 7200, -85)
        self.bufferChecker(weird1, 10800, -151)


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestBuffer))
    suite.addTest(makeSuite(TestTimedBuffer))
    return suite
