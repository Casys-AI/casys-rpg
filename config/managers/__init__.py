"""Manager configuration package."""
from config.managers.manager_config_base import ManagerConfigBase
from config.managers.agent_manager_config import AgentManagerConfig

__all__ = [
    'ManagerConfigBase',
    'AgentManagerConfig'
]
