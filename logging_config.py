import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
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
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True
        },
        'app': {  # logger spécifique pour app.py
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        },
        'agents': {  # logger pour tous les agents
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        },
        'story_graph': {  # logger pour story_graph.py
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        },
        'openai': {  # logger pour les appels OpenAI
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False
        },
        'httpx': {  # logger pour les requêtes HTTP
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False
        },
        'httpcore': {  # logger pour HTTP core
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False
        }
    }
}

def setup_logging():
    """Configure le logging pour toute l'application"""
    logging.config.dictConfig(LOGGING_CONFIG)
