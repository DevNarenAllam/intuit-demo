import datetime


def current_time():
    return datetime.datetime.now(datetime.timezone.utc)


class TokenBucket:
    """
    A class to implement the Token Bucket algorithm for rate limiting.

    Attributes:
        capacity (int): The maximum number of tokens the bucket can hold.
        tokens (int): The current number of tokens in the bucket.
        refill_rate (float): The rate at which tokens are added to the bucket (tokens per second).
        last_refill_timestamp (float): The timestamp of the last token refill.

    Methods:
        __init__(capacity, refill_rate):
            Initializes the TokenBucket with a specified capacity and refill rate.

        allow_request():
            Checks if a request can be allowed based on the current number of tokens.
            Returns True if the request is allowed, otherwise False.

        refill_tokens():
            Refills the bucket with tokens based on the elapsed time since the last refill.
    """

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
    """
    A class to implement the Leaky Bucket rate limiting algorithm.

    Attributes:
    -----------
    capacity : int
        The maximum number of requests that can be held in the bucket.
    leak_rate : float
        The rate at which requests are processed (leaked) from the bucket.
    queue : list
        A list to hold the incoming requests.
    last_leak_timestamp : float
        The timestamp of the last leak operation.

    Methods:
    --------
    __init__(capacity, leak_rate):
        Initializes the LeakyBucket with a specified capacity and leak rate.
    allow_request(request):
        Checks if a request can be allowed based on the current state of the bucket.
    leak():
        Processes (leaks) requests from the bucket based on the elapsed time and leak rate.
    """

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
    """
    A rate limiter that uses a fixed window strategy.

    Attributes:
        limit (int): The maximum number of requests allowed within the window.
        window_size (int): The size of the window in seconds.
        counter (int): The current count of requests in the current window.
        window_start (float): The start time of the current window.

    Methods:
        __init__(limit, window_size):
            Initializes the FixedWindow with a limit and window size.

        allow_request():
            Determines if a request is allowed based on the current count and window size.
            Returns True if the request is allowed, otherwise False.
    """

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
