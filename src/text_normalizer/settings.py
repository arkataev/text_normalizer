from os import path, environ

DEBUG = int(environ.get('DEBUG', 0))
ROOT_PATH = path.normpath(environ.get("TEXT_NORMALIZER_PATH", path.dirname(__file__)))
DATA_PATH = path.join(ROOT_PATH, 'data')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'base': {
            'format': '%(asctime)s %(name)s [%(levelname)s] : %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s %(name)s [%(levelname)s] PID-%(process)d %(message)s'
        },
        'module': {
            'format': '%(asctime)s %(name)s [%(levelname)s] %(module)s PID-%(process)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'module': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'module',
        },
    },
    'loggers': {
        'rtn_server': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'perflog': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'rtn': {
            'handlers': ['module'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'mptn': {
            'handlers': ['module'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        }
    }
}
