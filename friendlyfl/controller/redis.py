import redis as redis

from friendlyfl.settings import REDIS_HOST, REDIS_PORT, REDIS_DB

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def get_redis():
    return redis.Redis(connection_pool=pool)
