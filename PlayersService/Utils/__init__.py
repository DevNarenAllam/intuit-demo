class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill_timestamp = current_time()

    def allow_request(self):
        self.refill_tokens()
        if self.tokens > 0:
            self.tokens -= 1
            return True
        return False

    def refill_tokens(self):
        now = current_time()
        elapsed = now - self.last_refill_timestamp
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_timestamp = now


class LeakyBucket:
    def __init__(self, capacity, leak_rate):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.queue = []
        self.last_leak_timestamp = current_time()

    def allow_request(self, request):
        self.leak()
        if len(self.queue) < self.capacity:
            self.queue.append(request)
            return True
        return False

    def leak(self):
        now = current_time()
        elapsed = now - self.last_leak_timestamp
        leaks = elapsed * self.leak_rate
        for _ in range(int(leaks)):
            if self.queue:
                self.queue.pop(0)
        self.last_leak_timestamp = now


class FixedWindow:
    def __init__(self, limit, window_size):
        self.limit = limit
        self.window_size = window_size
        self.counter = 0
        self.window_start = current_time()

    def allow_request(self):
        if current_time() >= self.window_start + self.window_size:
            self.window_start = current_time()
            self.counter = 1
            return True
        elif self.counter < self.limit:
            self.counter += 1
            return True
        return False
