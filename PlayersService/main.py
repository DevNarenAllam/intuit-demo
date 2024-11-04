from contextlib import asynccontextmanager
import datetime
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from Common import get_service_logger
from Common import SERVICE_NAME
from sqlmodel import Session, select
from typing import List
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from .models import Players, get_session, create_tables
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Define constants for rate limiting
RATE_LIMIT = 5  # Maximum requests
RATE_PERIOD = 60
# Define constants for throttling
THROTTLE_LIMIT = 5  # Max requests within throttle period
THROTTLE_PERIOD = 60  # Throttle period in seconds (e.g., 1 minute)
COOLDOWN_PERIOD = 30  # Cooldown period after limit is exceeded
# Initialize logger
logger = get_service_logger(SERVICE_NAME)


redis_pool = redis.ConnectionPool.from_url(
    "redis://localhost", decode_responses=True, max_connections=10
)
redis_client = redis.Redis(connection_pool=redis_pool)


async def custom_key_builder(func, namespace: str, request: Request, *args, **kwargs):
    # Build the cache key based on the endpoint path and query parameters
    cache_key = f"{namespace}:{func.__name__}:{request.url.path}"
    # Add each query parameter to the cache key for uniqueness
    query_params = "&".join(
        [f"{key}={value}" for key, value in request.query_params.items()]
    )
    return f"{cache_key}?{query_params}"


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()

    await redis_client.ping()

    await FastAPILimiter.init(redis_client)
    FastAPICache.init(
        RedisBackend(redis_client),
        prefix="fastapi-cache",
        key_builder=custom_key_builder,
    )
    yield
    await FastAPILimiter.close()
    await redis_pool.disconnect()


app = FastAPI(lifespan=lifespan)


async def check_rate_limit(ip: str, redis):
    key = f"rate_limit:{ip}"

    # Track the number of requests from the IP
    current = await redis.get(key)

    if current and int(current) >= RATE_LIMIT:
        return False  # Rate limit exceeded

    # Increment count and set expiry if it's a new key
    pipeline = redis.pipeline()
    pipeline.incr(key)
    pipeline.expire(key, RATE_PERIOD)
    await pipeline.execute()

    return True


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host

    # Check if rate limit is exceeded
    if not await check_rate_limit(client_ip, redis_client):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Process the request if within limit
    response = await call_next(request)
    return response


async def check_throttle(ip: str, redis):
    key = f"throttle:{ip}"

    # Get current request count and cooldown end time
    current = await redis_client.get(key)
    current_time = datetime.datetime.now(datetime.timezone.utc)

    # Parse the value if it exists

    if current:
        count, reset_time = current.split(":", 1)
        count = float(count)
        reset_time = datetime.strptime(reset_time, "%Y-%m-%d %H:%M:%S.%f%z")

        # Check if user is in cooldown period
        if current_time < reset_time:
            return False, reset_time - current_time

        # Reset if throttle period has passed
        if current_time >= reset_time:
            count = 0

    else:
        count, reset_time = 0, current_time + datetime.timedelta(
            seconds=THROTTLE_PERIOD
        )

    # Increment request count
    count += 1

    # If limit exceeded, set cooldown
    if count > THROTTLE_LIMIT:
        reset_time = current_time + datetime.timedelta(seconds=COOLDOWN_PERIOD)
        count = 0  # Reset the count to start fresh after cooldown

    # Store the new count and reset time in Redis
    await redis_client.set(
        key,
        f"{count}:{reset_time}",
        ex=max(int((reset_time - current_time).seconds), 1),
    )

    return True, None


@app.middleware("http")
async def throttle_middleware(request: Request, call_next):
    client_ip = request.client.host

    # Check if throttle limit is exceeded
    allowed, cooldown_time = await check_throttle(client_ip, redis_client)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Please wait {int(cooldown_time)} seconds.",
        )

    # Process the request if within limit
    response = await call_next(request)
    return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def custom_identifier(request: Request) -> str:
    return request.client.host


@app.get(
    "/players/",
    tags=["players"],
    response_model=List[Players],
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
@cache(expire=60)
async def get_players(session: Session = Depends(get_session)):
    try:
        results = session.exec(select(Players)).all()
        return results

    except Exception as e:
        logger.error(f"Error in get_players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/players/{playerID}",
    tags=["players"],
    response_model=Players,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
@cache(expire=60)
async def get_players(
    playerID: str,
    session: Session = Depends(get_session),
):
    try:
        results = session.exec(
            select(Players).where(Players.playerID == playerID)
        ).first()
        return results

    except Exception as e:
        logger.error(f"Error in get_players: {e}")
        raise HTTPException(status_code=500, detail=str(e))
