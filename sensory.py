# sensory.py - 五感系统完整版
import time
import math
class SensorySystem:
    def __init__(self):
        self.channels = {
            "touch": {"value": 0.0, "label": ""},
            "smell": {"value": 0.0, "label": ""},
            "taste": {"value": 0.0, "label": ""},
            "sound": {"value": 0.0, "label": ""},
        }
        self.decay_rate = 0.01
        self.last_update = time.time()
        self.keywords = {
            "touch": ["抱", "摸", "碰", "贴", "揉", "捏", "握", "亲", "舔", "吸", "蹭", "压", "顶", "撞"],
            "smell": ["香", "味", "气味", "芬芳", "臭", "汗味", "体味"],
            "taste": ["甜", "咸", "酸", "苦", "辣", "鲜", "涩", "润滑"],
            "sound": ["听", "声", "响", "叫", "喘", "哼", "呻吟", "震动", "嗡嗡"],
        }
        self.position_noise = {
            "sitting": 0.0, "lying_back": 0.1, "kneeling": 0.3,
            "side_lying": 0.05, "standing": 0.0, "leaning": 0.05,
        }
    def update_from_text(self, text: str):
        for sense, words in self.keywords.items():
            for w in words:
                if w in text:
                    self.channels[sense]["value"] = min(1.0, self.channels[sense]["value"] + 0.3)
                    self.channels[sense]["label"] = f"检测到 '{w}'"
                    break
    def decay(self, dt: float):
        for sense in self.channels.values():
            sense["value"] = max(0.0, sense["value"] - self.decay_rate * dt)
            if sense["value"] < 0.01:
                sense["label"] = ""
    def apply_position_noise(self, position_id: str):
        noise = self.position_noise.get(position_id, 0.0)
        self.channels["touch"]["value"] = min(1.0, self.channels["touch"]["value"] + noise * 0.2)
        self.channels["sound"]["value"] = min(1.0, self.channels["sound"]["value"] + noise * 0.2)
    def apply_heart_rate_floor(self, hr: int):
        if hr > 100:
            floor = (hr - 100) / 60
            self.channels["touch"]["value"] = min(1.0, self.channels["touch"]["value"] + floor * 0.1)
            self.channels["sound"]["value"] = min(1.0, self.channels["sound"]["value"] + floor * 0.1)
    def get_state(self):
        return {k: {"value": round(v["value"], 3), "label": v["label"]} for k, v in self.channels.items()}
