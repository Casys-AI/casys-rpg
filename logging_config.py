import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        },
        'api': {  # logger spécifique pour api.py
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'agents': {  # logger pour tous les agents
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        },
        'story_graph': {  # logger pour story_graph.py
            'handlers': ['console'],
            'level': 'INFO',
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
