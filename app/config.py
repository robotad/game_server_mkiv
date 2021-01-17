import logging
import os

def str_to_bool(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    else:
        raise ValueError # evil ValueError that doesn't tell you what the wrong value was


ENDIAN='<'

DEV_ASYNC_DEBUG_LOG = str_to_bool(os.getenv('DEV_ASYNC_DEBUG_LOG'))
DEV_LOG = str_to_bool(os.getenv('DEV_LOG'))
DEV_PROFILE = str_to_bool(os.getenv('DEV_PROFILE', default='False'))
DEV_IS_LOCAL_DOCKER = str_to_bool(os.getenv('DEV_IS_LOCAL_DOCKER'))

UDP_EXTERNAL_HOST = os.getenv('UDP_EXTERNAL_HOST')
UDP_RECV_PORT = int(os.getenv('UDP_RECV_PORT'))

LOG_LEVEL = os.getenv('LOG_LEVEL')
logging.basicConfig()
log = logging.getLogger()
if LOG_LEVEL.lower() == "debug" or DEV_ASYNC_DEBUG_LOG:
    log.setLevel(logging.DEBUG)
elif LOG_LEVEL.lower() == "info":
    log.setLevel(logging.INFO)
elif LOG_LEVEL.lower() == "warn":
    log.setLevel(logging.WARN)

TEXT_GREEN = '\033[92m'
TEXT_CYAN = '\033[96m'
TEXT_BLUE = '\033[94m'
TEXT_RED = '\033[91m'
TEXT_ENDC = '\033[0m'