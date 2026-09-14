from collections import defaultdict, deque
from .config import SEQUENCE_LENGTH, FEATURES

class WindowManager:
    def __init__(self):
        self._windows = defaultdict(lambda: deque(maxlen=SEQUENCE_LENGTH))

    def add(self, reading):
        self._windows[reading.node_id].append(reading)
        return list(self._windows[reading.node_id])

    def size(self, node_id):
        return len(self._windows[node_id])

    @staticmethod
    def as_array(window):
        return [[float(getattr(item, feature)) for feature in FEATURES] for item in window]

windows = WindowManager()
