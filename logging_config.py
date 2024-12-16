import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': 'debug.log',
            'mode': 'a',
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True
        },
        'agents': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        },
        'EventBus': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        },
        '__main__': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        }
    }
}

def setup_logging():
    """Configure le logging pour toute l'application"""
    logging.config.dictConfig(LOGGING_CONFIG)
