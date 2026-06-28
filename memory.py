# memory.py - 记忆回路
import time
import json
import os
class MemorySystem:
    def __init__(self):
        self.last_intimacy_at = None
        self.intimacy_duration = 0
        self.morning_boost = 1.0
        self.env_sanctuary_memories = {}
        self.memory_file = "data/life/memory.json"
        self._load_memory()
    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    self.last_intimacy_at = data.get("last_intimacy_at")
                    self.intimacy_duration = data.get("intimacy_duration", 0)
                    self.morning_boost = data.get("morning_boost", 1.0)
                    self.env_sanctuary_memories = data.get("env_sanctuary_memories", {})
            except:
                pass
    def _save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump({
                "last_intimacy_at": self.last_intimacy_at,
                "intimacy_duration": self.intimacy_duration,
                "morning_boost": self.morning_boost,
                "env_sanctuary_memories": self.env_sanctuary_memories,
            }, f)
    def record_intimacy(self, hr: int, duration: int):
        if hr >= 0.65 and duration > 3600:
            self.last_intimacy_at = time.time()
            self.intimacy_duration = duration
            self.morning_boost = 1.6
            self._save_memory()
    def get_morning_boost(self):
        if self.last_intimacy_at and (time.time() - self.last_intimacy_at) < 86400:
            return self.morning_boost
        return 1.0
    def record_env_sanctuary(self, env_id: str):
        if env_id not in self.env_sanctuary_memories:
            self.env_sanctuary_memories[env_id] = []
        self.env_sanctuary_memories[env_id].append(time.time())
        self._save_memory()
    def get_sanctuary_memories(self, env_id: str):
        return len(self.env_sanctuary_memories.get(env_id, []))
    def forge_filter(self, text: str) -> str:
        prefixes = ["[心跳]", "[生命体征]", "[toy-use-wake]"]
        for p in prefixes:
            if text.startswith(p):
                text = text[len(p):].lstrip()
        return text
