from unittest import TestCase, TestSuite, makeSuite

from mtj.multimer.buffer import Buffer, TimedBuffer

qSilo = lambda value, full: TimedBuffer(delta=100, period=3600, timestamp=0,
    delta_min=0, delta_factor=1, value=value, full=full)
qSiloDM = lambda value, full: TimedBuffer(delta=100, period=3600, timestamp=0,
    delta_min=0.01, delta_factor=1, value=value, full=full)
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

    def test_0001_instance(self):
        buf = Buffer(value=50, full=200, empty=10)
        newbuf = buf.getCurrent(value=buf.value)
        self.assertTrue(isinstance(newbuf, Buffer))
        self.assertEqual(newbuf.value, buf.value)
        self.assertEqual(newbuf.full, buf.full)
        self.assertEqual(newbuf.empty, buf.empty)

    def test_0010_assertions(self):
        self.assertRaises(AssertionError, Buffer, empty=10)
        self.assertRaises(AssertionError, Buffer, value=10000, full=200)
        self.assertRaises(AssertionError, Buffer, value=-1000, empty=-200)


class TestTimedBuffer(TestCase):

    def setUp(self):
        self.full_silo = qSilo(60000, 60000)
        self.part_silo = qSilo(1234, 60000)
        self.zero_silo = qSilo(0, 60000)

        self.full_silodm = qSiloDM(60000, 60000)
        self.part_silodm = qSiloDM(1234, 60000)
        self.zero_silodm = qSiloDM(0, 60000)

        self.full_pos = qLPos(28000)
        self.part_pos = qLPos(1234)
        self.zero_pos = qLPos(0)

    def tearDown(self):
        pass

    def bufferChecker(self, buff, timestamp, value, freeze=None):
        next_buffer = buff.getCurrent(timestamp)
        self.assertTrue(isinstance(next_buffer, TimedBuffer))
        self.assertEqual(next_buffer.value, value)
        if freeze is not None:
            self.assertEqual(next_buffer.isToBeFrozen(timestamp), freeze)

    def test_0000_assertions(self):
        self.assertRaises(AssertionError, TimedBuffer, period=0)
        self.assertRaises(AssertionError, TimedBuffer, delta_min=-1)

    def test_0001_base_get(self):
        fp0 = self.full_pos.getCurrent(0)

        self.assertEqual(fp0.delta, self.full_pos.delta)
        self.assertEqual(fp0.period, self.full_pos.period)
        self.assertEqual(fp0.timestamp, self.full_pos.timestamp)
        self.assertEqual(fp0.delta_min, self.full_pos.delta_min)
        self.assertEqual(fp0.delta_factor, self.full_pos.delta_factor)
        self.assertEqual(fp0.freeze, self.full_pos.freeze)
        self.assertEqual(fp0.full, self.full_pos.full)
        self.assertEqual(fp0.empty, self.full_pos.empty)
        self.assertEqual(fp0.value, self.full_pos.value)

    def test_0050_full_continuous(self):
        """
        Test that intermediate buffers can be chained properly.
        """

        fp0 = self.full_pos.getCurrent(0)
        # half hour.
        fp1 = fp0.getCurrent(3600)
        fp2 = fp1.getCurrent(7200)
        self.assertEqual(fp2.getCurrent(7200).value, 27920)

    def test_0100_standard_inc(self):
        self.bufferChecker(self.zero_silo, 1, 0)
        self.bufferChecker(self.zero_silo, 3600, 100)
        self.bufferChecker(self.zero_silo, 35999, 900)
        self.bufferChecker(self.zero_silo, 36000, 1000, False)
        self.bufferChecker(self.zero_silo, 2159999, 59900, False)
        self.bufferChecker(self.zero_silo, 2160000, 60000, False)
        self.bufferChecker(self.zero_silo, 2163600, 60000, True)

    def test_0101_standard_inc(self):
        self.bufferChecker(self.part_silo, 1, 1234)
        self.bufferChecker(self.part_silo, 3600, 1334)
        self.bufferChecker(self.part_silo, 35999, 2134)
        self.bufferChecker(self.part_silo, 36000, 2234)
        self.bufferChecker(self.part_silo, 2113200, 59934)
        self.bufferChecker(self.part_silo, 2116799, 59934, False)
        # This pushed it over the top.
        self.bufferChecker(self.part_silo, 2116800, 60000, True)
        self.bufferChecker(self.part_silo, 2120399, 60000, True)
        self.bufferChecker(self.part_silo, 2120400, 60000, True)
        self.bufferChecker(self.part_silo, 2160000, 60000)

    def test_0102_standard_inc(self):
        self.bufferChecker(self.full_silo, 1, 60000, False)
        self.bufferChecker(self.full_silo, 3600, 60000, True)
        self.bufferChecker(self.full_silo, 7201, 60000, True)

    def test_0110_standard_inc_dm(self):
        self.bufferChecker(self.zero_silodm, 1, 0)
        self.bufferChecker(self.zero_silodm, 3600, 100)
        self.bufferChecker(self.zero_silodm, 35999, 900)
        self.bufferChecker(self.zero_silodm, 36000, 1000, False)
        self.bufferChecker(self.zero_silodm, 2159999, 59900, False)
        self.bufferChecker(self.zero_silodm, 2160000, 60000, False)
        self.bufferChecker(self.zero_silodm, 2163600, 60000, True)

    def test_0111_standard_inc_dm(self):
        self.bufferChecker(self.part_silodm, 1, 1234)
        self.bufferChecker(self.part_silodm, 3600, 1334)
        self.bufferChecker(self.part_silodm, 35999, 2134)
        self.bufferChecker(self.part_silodm, 36000, 2234)
        self.bufferChecker(self.part_silodm, 2113200, 59934)
        self.bufferChecker(self.part_silodm, 2116799, 59934, False)
        self.bufferChecker(self.part_silodm, 2116800, 60000, True)
        self.bufferChecker(self.part_silodm, 2120399, 60000, True)
        self.bufferChecker(self.part_silodm, 2120400, 60000, True)
        self.bufferChecker(self.part_silodm, 2160000, 60000)

    def test_0112_standard_inc_dm(self):
        self.bufferChecker(self.full_silodm, 1, 60000, False)
        self.bufferChecker(self.full_silodm, 3600, 60000, True)
        self.bufferChecker(self.full_silodm, 7201, 60000, True)

    def test_0200_standard_dec(self):
        self.bufferChecker(self.full_pos, 1, 28000)
        self.bufferChecker(self.full_pos, 3599, 28000)
        self.bufferChecker(self.full_pos, 3600, 27960)
        self.bufferChecker(self.full_pos, 3600, 27960)
        self.bufferChecker(self.full_pos, 252000, 25200)
        self.bufferChecker(self.full_pos, 2519999, 40, False)
        self.bufferChecker(self.full_pos, 2520000, 0, False)
        self.bufferChecker(self.full_pos, 2523599, 0, False)
        self.bufferChecker(self.full_pos, 2523600, 0, True)

    def test_0201_standard_dec(self):
        self.bufferChecker(self.part_pos, 1, 1234)
        self.bufferChecker(self.part_pos, 3600, 1194)
        self.bufferChecker(self.part_pos, 107999, 74, False)
        self.bufferChecker(self.part_pos, 108000, 34, False)
        self.bufferChecker(self.part_pos, 111599, 34, False)
        self.bufferChecker(self.part_pos, 111600, 34, True)

    def test_0202_standard_dec(self):
        self.bufferChecker(self.zero_pos, 1, 0, False)
        self.bufferChecker(self.zero_pos, 3600, 0, True)
        self.bufferChecker(self.zero_pos, 36000, 0, True)

    def test_0500_freeze(self):
        freeze = TimedBuffer(delta=100, period=3600, timestamp=0,
            delta_min=0.01, delta_factor=1, value=34567, full=75000,
            freeze=True)
        self.bufferChecker(freeze, 1, 34567, True)
        self.bufferChecker(freeze, 100000, 34567, True)
        timestamp = 200000
        next_buffer = freeze.getCurrent(timestamp, None)  # unspecified
        self.assertTrue(next_buffer.freeze)

    def test_0510_freeze(self):
        buff = TimedBuffer(delta=100, period=3600, timestamp=0,
            delta_min=0.01, delta_factor=1, value=34567, full=75000)

        timestamp = 14400
        next_buffer = buff.getCurrent(timestamp, None)  # unspecified
        self.assertEqual(next_buffer.value, 34967)
        self.assertEqual(next_buffer.isToBeFrozen(timestamp), False)

        timestamp = 7200
        next_buffer = buff.getCurrent(timestamp, True)
        self.assertTrue(next_buffer.freeze)
        self.assertEqual(next_buffer.value, 34767)
        # Frozen with less time less than above because it was forced
        # here.
        self.assertEqual(next_buffer.isToBeFrozen(timestamp), True)

    def test_0520_unfreeze(self):
        freeze = TimedBuffer(delta=100, period=3600, timestamp=0,
            delta_min=0.01, delta_factor=1, value=34567, full=75000,
            freeze=True)
        timestamp = 7201
        next_buffer = freeze.getCurrent(timestamp, False)
        self.assertFalse(next_buffer.freeze)
        timestamp = 14400
        # Unfrozen from 7201 onwards, 2 hours - second passed, +100.
        self.bufferChecker(next_buffer, timestamp, 34667, False)

    def test_1000_abnormal_setup(self):
        weird1 = TimedBuffer(delta=40, period=3600, timestamp=0,
            delta_min=0.325, delta_factor=-1, value=140, full=1000)
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
        self.bufferChecker(weird1, 32400, 981, True)

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
