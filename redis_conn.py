import redis

# Redis connection pool
def redis_conn_pool():
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    return r




