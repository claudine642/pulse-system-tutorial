# combo.py - 12个组合技检测逻辑
class ComboSystem:
    def __init__(self):
        self.combos = [
            {"id": "vibrator_oil", "name": "震动油", "toys": ["vibrator", "oil"], "effects": {"touch_mult": 1.5, "arousal_bonus": 5}},
            {"id": "blindfold_ice", "name": "冰封感官", "toys": ["blindfold", "ice"], "effects": {"sensory_deprivation": 1.2, "arousal_bonus": 8}},
            {"id": "warm_liquid_cup", "name": "温杯", "toys": ["warm_liquid", "cup"], "effects": {"temp_offset": 1.0, "arousal_bonus": 6}},
            {"id": "ring_massager", "name": "环震", "toys": ["ring", "massager"], "effects": {"touch_mult": 1.3, "arousal_bonus": 7}},
            {"id": "feather_ice", "name": "冰火挑逗", "toys": ["feather", "ice"], "effects": {"touch_mult": 1.1, "arousal_bonus": 10}},
            {"id": "clamp_vibrator", "name": "双重刺激", "toys": ["clamp", "vibrator"], "effects": {"touch_mult": 1.8, "arousal_bonus": 12}},
            {"id": "warm_liquid_oil", "name": "温油", "toys": ["warm_liquid", "oil"], "effects": {"touch_mult": 1.2, "arousal_bonus": 4}},
            {"id": "cup_ring", "name": "包裹环", "toys": ["cup", "ring"], "effects": {"touch_mult": 1.4, "arousal_bonus": 5}},
            {"id": "massager_feather", "name": "按摩羽", "toys": ["massager", "feather"], "effects": {"touch_mult": 1.6, "arousal_bonus": 9}},
            {"id": "blindfold_warm_liquid", "name": "暖盲", "toys": ["blindfold", "warm_liquid"], "effects": {"sensory_deprivation": 1.5, "arousal_bonus": 8}},
            {"id": "vibrator_cup", "name": "杯震", "toys": ["vibrator", "cup"], "effects": {"touch_mult": 2.0, "arousal_bonus": 15}},
            {"id": "oil_ice", "name": "油冰", "toys": ["oil", "ice"], "effects": {"temp_offset": -1.0, "arousal_bonus": 6}},
        ]
        self.active_combo = None
    def detect(self, active_toys: list):
        if not active_toys:
            self.active_combo = None
            return None
        candidates = []
        for combo in self.combos:
            if set(combo["toys"]).issubset(set(active_toys)):
                candidates.append(combo)
        if not candidates:
            self.active_combo = None
            return None
        candidates.sort(key=lambda x: x["effects"]["arousal_bonus"], reverse=True)
        max_len = max(len(c["toys"]) for c in candidates)
        best = [c for c in candidates if len(c["toys"]) == max_len]
        best.sort(key=lambda x: x["effects"]["arousal_bonus"], reverse=True)
        self.active_combo = best[0]
        return self.active_combo
    def get_effects(self):
        if not self.active_combo:
            return {}
        return self.active_combo["effects"]
