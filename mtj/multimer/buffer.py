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

    def getCurrent(self, value=None, *a, **kw):
        """
        Specify a current state of this buffer and return it as a copy.

        As full and empty values are considered immutable, they cannot
        be specified.
        """

        if value is None:
            value = self.value

        return self.__class__(
            full=self.full, 
            value=value,
            empty=self.empty,
            *a, **kw)


class TimedBuffer(Buffer):
    """
    A buffer hooked into some time.

    This buffer effectively a state of some buffer at some time, the
    period of which this buffer changes, and the delta to apply.
    """

    def __init__(self, delta=1, period=60, timestamp=None, delta_min=0,
            delta_factor=1, freeze=False, *a, **kw):
        """
        delta - the change in value made per period of time.
        period - the length of time between application of delta.
        timestamp - the timestamp for which the value was valid (unix
                    time)
        delta_min - minimum applied delta size, expressed as a fraction
                    of delta.
        delta_factor - post calculation modifier to delta.
        freeze - The timer is frozen onwards from timestamp.
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
        self.freeze = freeze

        self.freezePrefix = 'freeze'

        super(TimedBuffer, self).__init__(*a, **kw)

    def isToBeFrozen(self, timestamp=None, freeze=None):
        """
        Return whether the next state will be frozen.
        """

        def isFreezeMethod(attrname, prefix=self.freezePrefix):
            return attrname.startswith(prefix) and \
                hasattr(getattr(self, attrname), '__call__')
        freeze_method_names = filter(isFreezeMethod, dir(self))

        if freeze is True:
            # Freeze always wins.
            return freeze

        # only calculate if not True.
        for fname in freeze_method_names:
            f = getattr(self, fname)
            if f(timestamp):
                return True

        # If unspecified, return the false value.
        return freeze is None and self.freeze

    def getDeltaTime(self, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())
        return timestamp - self.timestamp

    def getCyclesElapsed(self, timestamp=None):
        if self.freeze:
            return 0

        delta_t = self.getDeltaTime(timestamp)
        return int(delta_t / self.period)  # truncate decimals.

    def getCyclesAvailable(self):
        if self.freeze:
            return 0
        return self.getCyclesPossible()

    def getCyclesPossible(self):
        if self.delta_factor < 0:
            # This is a funny way to do casting/truncating.
            return int((self.value - self.empty) * 1.0 / self.delta)
        elif self.delta_factor > 0:
            return int((self.full - self.value) * 1.0 / self.delta)

    def getCyclesRemaining(self, timestamp=None):
        return self.getCyclesAvailable() - self.getCyclesElapsed(timestamp)

    def isCyclesDepleted(self, timestamp=None):
        # must be negative to be considered depleted.
        return self.getCyclesRemaining(timestamp) < 0

    def freeze_CyclesDepleted(self, timestamp):
        return self.isCyclesDepleted(timestamp=timestamp)

    def getCurrent(self, timestamp=None, freeze=None, *a, **kw):
        """
        Returns a current version of this buffer.

        Timestamp defaults to current time unless it is specified.
        """

        # Freeze the time for the duration of this method.
        if timestamp is None:
            timestamp = int(time.time())

        cycles_elapsed = self.getCyclesElapsed(timestamp)
        cycles_available = self.getCyclesAvailable()
        cycles_depleted = self.isCyclesDepleted(timestamp)
        # Figure this out if we are not freezing this.
        freeze = self.isToBeFrozen(timestamp, freeze)

        safe_value = self.value + (cycles_available * self.delta)

        if self.delta_factor < 0:
            remainder = (self.value - self.empty) % self.delta
        elif self.delta_factor > 0:
            remainder = (self.full - self.value) % self.delta

        # Must be at least 1.
        subdelta = max(int(round(self.delta * self.delta_min)), 1)
        subcycles = remainder / subdelta

        # Only apply subcycles after all available cycles are consumed.
        value = (self.value + (min(cycles_elapsed, cycles_available) * 
            self.delta + (subcycles * subdelta * int(cycles_depleted))) *
            self.delta_factor)

        try:
            result = super(TimedBuffer, self).getCurrent(
                delta=self.delta,
                period=self.period,
                timestamp=timestamp,
                delta_min=self.delta_min,
                delta_factor=self.delta_factor,
                value=value,
                freeze=freeze,
                *a, **kw
            )
        except AssertionError, e:
            raise RuntimeError('There are bugs in the buffer implementation.')

        return result
