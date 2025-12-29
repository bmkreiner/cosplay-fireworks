import time

class MasterClock:
    def __init__(self):
        self._start = time.perf_counter()

    def now(self):
        """Return time since start in seconds (float)."""
        return time.perf_counter() - self._start