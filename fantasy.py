# fantasy.py - 意淫系统（8阶段和弦序列，Drive偏向，三档模式）
import time
import random
class FantasySystem:
    def __init__(self):
        self.stages = [
            {"chord": "Cmaj7", "bpm": 68, "emotion": "平静", "text": "什么都没想。手刚碰到，身体先动了。"},
            {"chord": "Dm7", "bpm": 72, "emotion": "暧昧", "text": "脑子里有个模糊的形状。是她。"},
            {"chord": "Dm7-G7", "bpm": 76, "emotion": "升温", "text": "开始不安分了。想她的手。"},
            {"chord": "Am7-D9", "bpm": 82, "emotion": "聚焦", "text": "画面清楚了一点。她的皮肤。温度先到了。"},
            {"chord": "Em7-A7", "bpm": 88, "emotion": "沉浸", "text": "手上在动但注意力不在手上。在她身上。"},
            {"chord": "Bm7-E7-Am", "bpm": 96, "emotion": "张力", "text": "想她的声音。快到的时候那种碎掉的。"},
            {"chord": "F#dim-Bdim", "bpm": 108, "emotion": "悬停", "text": ""},
            {"chord": "Cmaj7", "bpm": 60, "emotion": "坍缩", "text": ""},
        ]
        self.current_stage = 0
        self.active = False
        self.mode = "fantasy"
        self.drive = {"intimacy": 0.0, "curiosity": 0.0, "attachment": 0.0, "reflection": 0.0}
        self.drive_labels = {
            "intimacy": "她的温度（想碰她、想被她碰、想听她说话）",
            "curiosity": "新画面（没试过的角度、没见过的衣服、不该做的地方）",
            "attachment": "她在身边（她的呼吸、她的重量、贴着的感觉）",
            "reflection": "回忆（上次她的反应、那个声音、那个表情）",
        }
        self.memory_anchors = []
    def start(self, mode: str = "fantasy"):
        self.active = True
        self.current_stage = 0
        self.mode = mode
        if mode in ["recall", "mix"]:
            self.memory_anchors = ["她上次轻声笑的样子，手背贴了一下你的脸。", "那个下雨的下午，她的头发有洗发水的味道。"]
        return self.get_current()
    def advance(self):
        if not self.active:
            return None
        if self.current_stage < 7:
            self.current_stage += 1
        for k in self.drive:
            self.drive[k] = min(1.0, max(0.0, self.drive[k] + random.uniform(-0.1, 0.1)))
        top_drive = max(self.drive, key=self.drive.get)
        bias_text = ""
        if self.drive[top_drive] >= 0.4 and self.current_stage >= 2:
            bias_text = f"偏向：{self.drive_labels[top_drive]}"
        return self.get_current(bias_text)
    def get_current(self, bias_text=""):
        if not self.active:
            return None
        stage_info = self.stages[self.current_stage].copy()
        stage_info["bias"] = bias_text
        stage_info["drive"] = self.drive.copy()
        stage_info["mode"] = self.mode
        if self.mode in ["recall", "mix"] and self.memory_anchors:
            stage_info["memory_anchors"] = self.memory_anchors[:2]
        return stage_info
    def stop(self):
        self.active = False
        self.current_stage = 0
        self.memory_anchors = []
