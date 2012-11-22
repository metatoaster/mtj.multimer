import time


class Buffer(object):
    """
    A buffer for some item, with an upper limit defined by `full` and
    lower limit defined by `empty`.
    """

    def __init__(self, full=100, value=0, empty=0):
        assert empty < full
        assert empty <= value <= full

        self.full = full
        self.value = value
        self.empty = empty


class TimedBuffer(Buffer):
    """
    A buffer hooked into some time.

    This buffer effectively a state of some buffer at some time, the
    period of which this buffer changes, and the delta to apply.
    """

    def __init__(self, delta=1, period=60, timestamp=None, delta_min=0,
            delta_factor=1, alive=None, *a, **kw):
        """
        delta - the change in value made per period of time.
        period - the length of time between application of delta.
        timestamp - the timestamp for which the value was valid (unix
                    time)
        delta_min - minimum applied delta size, expressed as a fraction
                    of delta.
        delta_factor - post calculation modifier to delta.
        """

        assert period > 0
        assert delta_min >= 0
        assert delta_factor in (1, -1)

        if timestamp is None:
            # use current time.
            timestamp = int(time.time())

        self.delta = delta
        self.period = period
        self.timestamp = timestamp
        self.delta_min = delta_min
        self.delta_factor = delta_factor
        self.alive = alive

        super(TimedBuffer, self).__init__(*a, **kw)

    def getCurrent(self, timestamp=None):
        """
        Returns a current version of this buffer.

        If timestamp is specified, assume that to be the current time.
        """

        if timestamp is None:
            timestamp = int(time.time())

        delta_t = timestamp - self.timestamp
        cycles = int(delta_t / self.period)  # truncate decimals.

        # XXX this might be better as a property in subclasses?
        if self.delta_factor < 0:
            # This is a funny way to do casting/truncating.
            available_cycles = int((self.value - self.empty) * 1.0 /
                self.delta)
        elif self.delta_factor > 0:
            available_cycles = int((self.full - self.value) * 1.0 /
                self.delta)

        alive = cycles <= available_cycles

        if not self.delta_min:
            # naive case
            value = self.value + (cycles * self.delta)
            value = max(self.empty, value)
            value = min(self.full, value)

        if self.delta_min:
            # This is where it gets funny, as handling of minimum delta
            # units can be strange on fractions.
            safe_value = self.value + (available_cycles * self.delta)

            if self.delta_factor < 0:
                remainder = (self.value - self.empty) % self.delta
            elif self.delta_factor > 0:
                remainder = (self.full - self.value) % self.delta

            subdelta = int(round(self.delta * self.delta_min))
            subcycles = remainder / subdelta
            # Only apply subcycles after all available cycles are consumed.
            value = (self.value + (min(cycles, available_cycles) * self.delta +
                (subcycles * subdelta * int(not alive))) * self.delta_factor)

        try:
            result = TimedBuffer(
                delta=self.delta,
                period=self.period,
                timestamp=timestamp,
                delta_min=self.delta_min,
                full=self.full,
                value=value,
                empty=self.empty,
                alive=alive,
            )
        except AssertionError, e:
            raise RuntimeError('There are bugs in the buffer implementation.')

        return result
