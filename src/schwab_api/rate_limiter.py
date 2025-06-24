import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=120, time_window=600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times = deque()

    def wait(self):
        now = time.time()
        while len(self.request_times) >= self.max_requests:
            if now - self.request_times[0] > self.time_window:
                self.request_times.popleft()
            else:
                time.sleep(1)
                now = time.time()
        self.request_times.append(now)