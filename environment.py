# environment.py - 环境系统（7基础+4季节限定，进化树，圣地记忆）
import time
import random
class EnvironmentSystem:
    def __init__(self):
        self.base_envs = {
            "candle": {"name": "烛光", "level": 1, "max_level": 3, "is_hidden": False, "memory_count": 0, "is_sanctuary": False},
            "rain": {"name": "雨声", "level": 1, "max_level": 3, "is_hidden": False, "memory_count": 0, "is_sanctuary": False},
            "fireplace": {"name": "壁炉", "level": 1, "max_level": 3, "is_hidden": False, "memory_count": 0, "is_sanctuary": False},
            "forest": {"name": "森林", "level": 1, "max_level": 3, "is_hidden": False, "memory_count": 0, "is_sanctuary": False},
            "ocean": {"name": "海潮", "level": 1, "max_level": 3, "is_hidden": False, "memory_count": 0, "is_sanctuary": False},
            "desert": {"name": "沙漠热风", "level": 1, "max_level": 3, "is_hidden": False, "memory_count": 0, "is_sanctuary": False},
            "snow": {"name": "雪境", "level": 1, "max_level": 3, "is_hidden": False, "memory_count": 0, "is_sanctuary": False},
        }
        self.seasonal_envs = {
            "spring_bloom": {"name": "春樱", "level": 1, "max_level": 2, "is_hidden": True, "memory_count": 0, "is_sanctuary": False},
            "summer_heat": {"name": "炎夏热浪", "level": 1, "max_level": 2, "is_hidden": True, "memory_count": 0, "is_sanctuary": False},
            "autumn_leaves": {"name": "秋叶", "level": 1, "max_level": 2, "is_hidden": True, "memory_count": 0, "is_sanctuary": False},
            "winter_chill": {"name": "冬夜寒霜", "level": 1, "max_level": 2, "is_hidden": True, "memory_count": 0, "is_sanctuary": False},
        }
        self.all_envs = {**self.base_envs, **self.seasonal_envs}
        self.active_env_id = "candle"
        self.usage_history = {env_id: [] for env_id in self.all_envs}
        self.evolution_thresholds = {1: 3, 2: 10}
    def activate(self, env_id: str):
        if env_id not in self.all_envs:
            return False
        self.active_env_id = env_id
        self.usage_history[env_id].append(time.time())
        self._check_evolution(env_id)
        if len(self.usage_history[env_id]) >= 3:
            self.all_envs[env_id]["is_sanctuary"] = True
        return True
    def _check_evolution(self, env_id: str):
        env = self.all_envs[env_id]
        count = len(self.usage_history[env_id])
        current_level = env["level"]
        if current_level < env["max_level"]:
            next_level = current_level + 1
            if count >= self.evolution_thresholds.get(current_level, 999):
                env["level"] = next_level
                return True
        return False
    def get_evolution_tree(self, env_id: str):
        env = self.all_envs.get(env_id)
        if not env:
            return None
        return {
            "current_level": env["level"],
            "max_level": env["max_level"],
            "next_level_usage": self.evolution_thresholds.get(env["level"], None),
            "current_usage": len(self.usage_history.get(env_id, [])),
            "is_sanctuary": env["is_sanctuary"],
            "memory_count": env.get("memory_count", 0),
        }
    def get_active(self):
        return self.all_envs.get(self.active_env_id)
    def list_all(self):
        return [{"id": k, **v} for k, v in self.all_envs.items()]
