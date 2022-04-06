import enum
from environs import Env

env = Env()
env.read_env()

API_PATH = '/api'
TICKET_PATH = 'ticket'
COMMENT_PATH = 'comment'


# Состояния тикета
class TicketState(enum.Enum):
    open = 'OPEN'
    answered = 'ANSWERED'
    closed = 'CLOSED'
    waiting = 'WAITING'


# Возможные переходы состояний тикета
state_transitions = {
    TicketState.open.value: (TicketState.answered.value, TicketState.closed.value),
    TicketState.answered.value: (TicketState.waiting, TicketState.closed.value)
}

# Текущий пользователь
TEST_USER = env('TEST_USER', 'mikhailova.anna.vadimovna@gmail.com')


# Конфигурация для БД
class PGConfig(object):
    PG_HOST = env('PG_HOST', 'localhost')
    PG_PORT = int(env('PG_PORT', 5432))
    PG_USER = env('PG_USER', 'postgres')
    PG_PASSWD = env('PG_PASSWD', 'mysecretpassword')
    PG_DATABASE = env('PG_DATABASE', 'postgres')


# Конфигурация для Redis
class CacheConfig(object):
    CACHE_TYPE = env('CACHE_TYPE', 'redis')
    CACHE_REDIS_HOST = env('CACHE_REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = env('CACHE_REDIS_PORT', 6379)
    CACHE_REDIS_DB = env('CACHE_REDIS_DB', 0)
    CACHE_REDIS_URL = env('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = env('CACHE_DEFAULT_TIMEOUT', 500)
