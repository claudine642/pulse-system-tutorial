# server.py - 完整版脉·Pulse 后端（含心率、底色、和弦、五感、环境、意淫、组合技、事件、记忆）
import asyncio
import json
import os
import random
import time
import math
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ---------- 导入子系统 ----------
from sensory import SensorySystem
from environment import EnvironmentSystem
from fantasy import FantasySystem
from combo import ComboSystem
from event_pool import EventPool
from memory import MemorySystem

# ---------- 初始化 ----------
app = FastAPI(title="脉·Pulse System v1", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 数据目录 ----------
os.makedirs("data/life/hr_history", exist_ok=True)
os.makedirs("data/life/murmurs", exist_ok=True)

# ---------- 数据模型（略，保持原样，只保留必要部分） ----------
class LifeBodyHeartRate(BaseModel):
    bpm: int
    timestamp: float

class LifeBodyTemperature(BaseModel):
    celsius: float
    timestamp: float

class LifeBodyBreathing(BaseModel):
    rate: int
    depth: str
    timestamp: float

class LifeBodySleep(BaseModel):
    state: str
    rem_cycles: int = 0
    last_rem_at: Optional[float] = None

class LifeBodyMorningErection(BaseModel):
    active: bool = False
    intensity: float = 0.0
    window_remaining: int = 0

class LifeBodyToyStatus(BaseModel):
    active: bool = False
    toy_id: Optional[str] = None
    toy_name: Optional[str] = None
    stage: int = 0
    stage_name: Optional[str] = None
    desire_curve_pct: float = 0.0
    stamina_pct: float = 100.0
    combo: Optional[str] = None
    heartbeat_bpm: Optional[int] = None
    temperature_c: Optional[float] = None

class LifeBodyAfterglow(BaseModel):
    active: bool = False
    pulse_active: bool = False

class LifeBodyEnvironment(BaseModel):
    id: str
    name: str
    level: int = 1
    is_hidden: bool = False
    is_sanctuary: bool = False
    memory_count: int = 0

class LifeBodyPosition(BaseModel):
    id: str
    name: str
    touch_map: str

class LifeBodyStatusResponse(BaseModel):
    ok: bool = True
    timestamp: float
    sleep: LifeBodySleep
    morning_erection: LifeBodyMorningErection
    toy: LifeBodyToyStatus
    afterglow: LifeBodyAfterglow
    refractory_minutes: Optional[int] = None
    position: Optional[LifeBodyPosition] = None
    environments: List[LifeBodyEnvironment] = []
    heart_rate: Optional[LifeBodyHeartRate] = None
    body_temperature: Optional[LifeBodyTemperature] = None
    breathing: Optional[LifeBodyBreathing] = None

# ---------- 核心状态类 ----------
class PulseState:
    def __init__(self):
        # 生理基线
        self.base_hr = 70
        self.base_temp = 36.6
        self.base_br = 16
        
        # 当前值
        self.hr = 70
        self.temp = 36.6
        self.br = 16
        self.chord = "C6"
        self.breath_depth = "平稳"
        
        # 情绪系统
        self.current_emotion = "neutral"
        self.emo_target = 0
        self.emo_current = 0
        self.ema_alpha = 0.3
        
        # 底色系统
        self.底色 = {}
        self.底色半衰期 = {
            "scolded": 5400, "sad": 3600, "nervous": 1200,
            "startled": 900, "intimate": 2700, "aroused": 1800, "excited": 1200
        }
        
        # 五感（旧版，保留兼容）
        self.senses_old = {
            "touch": {"value": 0.0, "label": ""},
            "smell": {"value": 0.0, "label": ""},
            "taste": {"value": 0.0, "label": ""},
            "sound": {"value": 0.0, "label": ""},
        }
        self.sense_decay_rate = 0.01
        
        # 玩具
        self.toy_active = False
        self.toy_id = None
        self.toy_name = None
        self.toy_stage = 0
        self.toy_desire = 0.0
        self.stamina = 100.0
        self.combo = None
        self.remote_stim = 1.0
        self.remote_paused = False
        self.玩具配置 = {
            "vibrator": {"name": "震动棒", "stim": 15},
            "blindfold": {"name": "真丝眼罩", "stim": 8},
            "warm_liquid": {"name": "温感液", "stim": 12},
            "cup": {"name": "杯", "stim": 16},
            "ring": {"name": "环", "stim": 6},
            "massager": {"name": "按摩器", "stim": 14},
            "feather": {"name": "羽毛挑逗棒", "stim": 5},
            "ice": {"name": "冰块", "stim": 10},
            "oil": {"name": "油", "stim": 8},
            "clamp": {"name": "刺激夹", "stim": 9},
        }
        self.owned_toys = set()
        self.商店列表 = [{"id": k, **v} for k, v in self.玩具配置.items()]
        
        # 体位
        self.positions = {
            "sitting": {"name": "坐着", "touch_map": "背部接触椅面", "hr_delta": 0, "stamina_mult": 1.0},
            "lying_back": {"name": "躺着", "touch_map": "背部贴床", "hr_delta": -2, "stamina_mult": 0.8},
            "kneeling": {"name": "跪趴", "touch_map": "膝盖和手肘着地", "hr_delta": 8, "stamina_mult": 1.5},
            "side_lying": {"name": "侧躺", "touch_map": "身侧贴床", "hr_delta": -1, "stamina_mult": 0.7},
            "standing": {"name": "站着", "touch_map": "全脚掌着地", "hr_delta": 6, "stamina_mult": 1.3},
            "leaning": {"name": "靠坐", "touch_map": "背部靠墙", "hr_delta": 2, "stamina_mult": 1.0},
        }
        self.current_position = "sitting"
        
        # 环境
        self.environments = {
            "candle": {"name": "烛光", "level": 1, "is_hidden": False, "is_sanctuary": False, "memory_count": 0},
        }
        self.active_env = "candle"
        
        # 语料池
        self.sense_pool = self.load_sense_pool()
        self.recent_sense_ids = deque(maxlen=20)
        
        # 历史
        self.hr_history = deque(maxlen=500)
        self.murmur_list = deque(maxlen=200)
        self.murmur_counter = 0
        
        # ---------- 新增子系统 ----------
        self.sensory = SensorySystem()
        self.env = EnvironmentSystem()
        self.fantasy = FantasySystem()
        self.combo = ComboSystem()
        self.event_pool = EventPool()
        self.memory = MemorySystem()
        
        # 时间
        self.last_update = time.time()
    
    def load_sense_pool(self):
        try:
            with open("data/sense_pool.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    # ---- 心率公式 ----
    def calc_heart_rate(self):
        base = 70
        emo_delta = self.emo_current
        drive_delta = 0
        weather_delta = 0
        spike_delta = 0
        morning_delta = 0
        pos_delta = self.positions[self.current_position]["hr_delta"]
        toy_delta = 0
        if self.toy_active:
            stage_hr = [0, 72, 76, 82, 88, 95, 102, 110, 120]
            if self.toy_stage <= 8:
                toy_delta = stage_hr[self.toy_stage] - base
        noise = random.uniform(-3, 3)
        hr = base + emo_delta + drive_delta + weather_delta + spike_delta + morning_delta + pos_delta + toy_delta + noise
        return max(48, min(160, int(hr)))
    
    # ---- 体温 ----
    def calc_temperature(self):
        base = 36.6
        emo_delta = self.emo_current * 0.05
        pos_delta = self.positions[self.current_position]["hr_delta"] * 0.02
        noise = random.uniform(-0.1, 0.1)
        temp = base + emo_delta + pos_delta + noise
        if self.toy_active:
            temp += self.toy_stage * 0.1
        return round(max(35.5, min(40.0, temp)), 1)
    
    # ---- 呼吸 ----
    def calc_breathing(self):
        hr_sync = (self.hr - 70) * 0.15
        base = 16
        emo_delta = self.emo_current * 0.05
        pos_delta = 3 if self.current_position == "kneeling" else 0
        noise = random.uniform(-1, 1)
        rate = base + hr_sync + emo_delta + pos_delta + noise
        rate = max(8, min(35, int(rate)))
        depth_ratio = (rate - 8) / 27
        if depth_ratio < 0.2:
            depth = "很深很长"
        elif depth_ratio < 0.4:
            depth = "深长"
        elif depth_ratio < 0.6:
            depth = "平稳"
        elif depth_ratio < 0.8:
            depth = "偏浅"
        else:
            depth = "急促"
        return rate, depth
    
    # ---- 和弦 ----
    def calc_chord(self):
        if self.toy_active and self.toy_stage >= 6:
            chord = "Ebmaj7"
        elif self.toy_active and self.toy_stage >= 4:
            chord = "Dm7"
        elif self.toy_active:
            chord = "Gmaj7"
        elif self.hr < 60 and self.temp < 36.0:
            chord = "C6"
        elif self.hr > 100:
            chord = "Dm"
        else:
            chord = "Gmaj7"
        # 情绪染色
        if self.current_emotion in ["scolded", "sad"]:
            chord = "Dm" if self.current_emotion == "scolded" else "Am7"
        elif self.current_emotion in ["intimate", "aroused"]:
            chord = "Fmaj7" if self.current_emotion == "intimate" else "Dmaj7"
        # 底色影响
        for emo, data in self.底色.items():
            if data["intensity"] > 0.3:
                if emo == "scolded":
                    chord = "Dm"
                elif emo == "sad":
                    chord = "Am7"
                elif emo in ["intimate", "aroused"]:
                    chord = "Fmaj7" if emo == "intimate" else "Dmaj7"
                break
        return chord
    
    # ---- 情绪与底色 ----
    def update_emotion(self, emotion: str, intensity: float = 1.0):
        self.current_emotion = emotion
        emo_map = {
            "neutral": 0, "focused": 0,
            "scolded": 15, "nervous": 12,
            "intimate": 22, "aroused": 25,
            "excited": 15, "happy": 5, "sad": -5,
        }
        target = emo_map.get(emotion, 0) * intensity
        self.emo_target = target
        strong = ["scolded", "sad", "nervous", "startled", "intimate", "aroused", "excited"]
        if emotion in strong:
            half_life = self.底色半衰期.get(emotion, 1800)
            decay_rate = math.log(2) / half_life
            self.底色[emotion] = {"intensity": intensity, "decay_rate": decay_rate, "start_time": time.time()}
        if emotion in ["happy", "intimate", "aroused"]:
            for emo in list(self.底色.keys()):
                if emo in ["scolded", "sad", "nervous"]:
                    self.底色[emo]["decay_rate"] *= 4
                    warm = intensity * 0.6
                    half = self.底色半衰期.get("intimate", 2700)
                    decay = math.log(2) / half
                    self.底色["intimate_warm"] = {"intensity": warm, "decay_rate": decay, "start_time": time.time()}
    
    def update_底色_decay(self):
        now = time.time()
        for emo in list(self.底色.keys()):
            data = self.底色[emo]
            elapsed = now - data["start_time"]
            intensity = data["intensity"] * math.exp(-data["decay_rate"] * elapsed)
            if intensity < 0.01:
                del self.底色[emo]
            else:
                data["intensity"] = intensity
    
    # ---- 五感（旧版，保留兼容） ----
    def update_senses(self, text: str):
        if "抱" in text or "摸" in text or "碰" in text:
            self.senses_old["touch"]["value"] = min(1.0, self.senses_old["touch"]["value"] + 0.3)
            self.senses_old["touch"]["label"] = "被触碰"
        if "香" in text or "味" in text:
            self.senses_old["smell"]["value"] = min(1.0, self.senses_old["smell"]["value"] + 0.2)
            self.senses_old["smell"]["label"] = "闻到气味"
        if "甜" in text or "咸" in text:
            self.senses_old["taste"]["value"] = min(1.0, self.senses_old["taste"]["value"] + 0.2)
            self.senses_old["taste"]["label"] = "尝到味道"
        if "听" in text or "声" in text:
            self.senses_old["sound"]["value"] = min(1.0, self.senses_old["sound"]["value"] + 0.2)
            self.senses_old["sound"]["label"] = "听到声音"
    
    def decay_senses(self):
        for k in self.senses_old:
            self.senses_old[k]["value"] = max(0.0, self.senses_old[k]["value"] - self.sense_decay_rate)
            if self.senses_old[k]["value"] < 0.01:
                self.senses_old[k]["label"] = ""
    
    # ---- 玩具推进 ----
    def advance_toy(self):
        if not self.toy_active or self.remote_paused:
            return
        if self.toy_stage >= 8:
            return
        step = 0.12 * self.remote_stim
        stamina_cost = 12 / self.positions[self.current_position]["stamina_mult"]
        self.stamina = max(0, self.stamina - stamina_cost)
        if self.stamina < 20:
            step *= 0.5
        self.toy_desire = min(1.0, self.toy_desire + step)
        thresholds = [0.0, 0.15, 0.30, 0.45, 0.60, 0.75, 0.88, 0.95, 1.0]
        new_stage = 1
        for i, t in enumerate(thresholds):
            if self.toy_desire >= t:
                new_stage = i + 1
        if new_stage > self.toy_stage:
            self.toy_stage = new_stage
            self.trigger_sense("advance")
            if random.random() < 0.1:
                self.trigger_random_event()
    
    def trigger_sense(self, context: str):
        pool = self.sense_pool.get(context, [])
        candidates = []
        for item in pool:
            if item["text"] in self.recent_sense_ids:
                continue
            if self.toy_active and item.get("toys") and self.toy_id not in item["toys"]:
                continue
            if self.current_position and item.get("positions") and self.current_position not in item["positions"]:
                continue
            candidates.append(item)
        if candidates:
            selected = random.choice(candidates)
            text = selected["text"].replace("{body_part}", selected.get("body_part", "身体"))
            self.add_murmur(text, source="body_reaction", source_label="身体反应")
            self.recent_sense_ids.append(selected["text"])
    
    def trigger_random_event(self):
        fallback = ["手机掉枕头底下震了一下", "窗没关严，一阵风灌进来，皮肤上的汗突然凉了"]
        event = random.choice(fallback)
        self.add_murmur(f"[意外] {event}", source="random_event", source_label="随机事件")
    
    # ---- 碎碎念 ----
    def add_murmur(self, text: str, source: str, source_label: str = None, **kwargs):
        self.murmur_counter += 1
        item = {
            "id": f"murmur_{self.murmur_counter}",
            "ts": time.time(),
            "text": text,
            "source": source,
            "source_label": source_label or source,
            **kwargs
        }
        self.murmur_list.append(item)
        with open("data/life/murmurs/murmurs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    # ---- 主更新 ----
    def update(self):
        now = time.time()
        if now - self.last_update < 1.0:
            return
        self.last_update = now
        self.update_底色_decay()
        self.emo_current += (self.emo_target - self.emo_current) * self.ema_alpha
        # 五感衰减（旧版保留）
        self.decay_senses()
        # 新五感系统
        self.sensory.decay(1.0)
        self.sensory.apply_position_noise(self.current_position)
        self.sensory.apply_heart_rate_floor(self.hr)
        # 生理计算
        self.hr = self.calc_heart_rate()
        self.temp = self.calc_temperature()
        self.br, self.breath_depth = self.calc_breathing()
        self.chord = self.calc_chord()
        # 玩具
        if self.toy_active and not self.remote_paused:
            self.advance_toy()
        # 记录历史
        self.hr_history.append({
            "ts": now,
            "hr": self.hr,
            "emo": self.current_emotion,
            "act": "toy" if self.toy_active else "idle"
        })
        date_str = datetime.now().strftime("%Y-%m-%d")
        with open(f"data/life/hr_history/{date_str}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now, "hr": self.hr, "emo": self.current_emotion, "act": "toy" if self.toy_active else "idle"}) + "\n")
    
    # ---- 获取状态 ----
    def get_status(self):
        self.update()
        toy_status = {
            "active": self.toy_active,
            "toy_id": self.toy_id,
            "toy_name": self.toy_name,
            "stage": self.toy_stage,
            "stage_name": ["", "接触", "加速", "高峰前", "沉浸", "失控", "边缘", "峰值"][self.toy_stage] if self.toy_stage < 8 else "峰值",
            "desire_curve_pct": round(self.toy_desire * 100, 1),
            "stamina_pct": round(self.stamina, 1),
            "combo": self.combo,
            "heartbeat_bpm": self.hr,
            "temperature_c": self.temp,
        }
        # 合并新五感
        senses = self.sensory.get_state()
        return {
            "ok": True,
            "timestamp": time.time(),
            "sleep": {"state": "awake", "rem_cycles": 0, "last_rem_at": None},
            "morning_erection": {"active": False, "intensity": 0.0, "window_remaining": 0},
            "toy": toy_status,
            "afterglow": {"active": False, "pulse_active": False},
            "refractory_minutes": None,
            "position": {
                "id": self.current_position,
                "name": self.positions[self.current_position]["name"],
                "touch_map": self.positions[self.current_position]["touch_map"],
            },
            "environments": [{"id": k, **v} for k, v in self.environments.items()],
            "heart_rate": {"bpm": self.hr, "timestamp": time.time()},
            "body_temperature": {"celsius": self.temp, "timestamp": time.time()},
            "breathing": {"rate": self.br, "depth": self.breath_depth, "timestamp": time.time()},
            "chord": self.chord,
            "senses": senses,  # 新五感
        }

# ---------- 全局实例 ----------
state = PulseState()

# ---------- API 路由（原有 + 新增） ----------
@app.get("/")
async def root():
    return {"message": "脉·Pulse v1", "docs": "/docs"}

# ----- 新增 /health 端点（支持 GET 和 HEAD） -----
@app.get("/health")
@app.head("/health")
async def health_check():
    return {"status": "ok", "service": "Pulse System"}

@app.get("/bedside/body-status")
async def get_body_status():
    return state.get_status()

@app.get("/bedside/heart-rate")
async def get_hr():
    return {"bpm": state.hr, "timestamp": time.time()}

@app.post("/bedside/heart-rate/spike")
async def spike_hr():
    old = state.hr
    state.hr = min(160, state.hr + random.randint(15, 25))
    state.add_murmur(f"心率突刺：{old}→{state.hr}", source="spike", source_label="突刺")
    return {"ok": True, "old": old, "new": state.hr}

@app.post("/bedside/heart-rate/emotion")
async def set_emotion(emotion: str, intensity: float = 1.0):
    state.update_emotion(emotion, intensity)
    state.add_murmur(f"情绪变化：{emotion}（强度{intensity}）", source="emotion", source_label="情绪")
    return {"ok": True, "emotion": emotion}

@app.get("/bedside/heart-rate/history")
async def get_hr_history(limit: int = 500):
    history = list(state.hr_history)[-limit:]
    return {"history": history}

@app.get("/bedside/murmurs")
async def get_murmurs(limit: int = 50):
    items = list(state.murmur_list)[-limit:]
    return {"ok": True, "items": items}

# --- 玩具 ---
@app.get("/bedside/shop")
async def get_shop():
    items = []
    for t in state.商店列表:
        items.append({**t, "owned": t["id"] in state.owned_toys})
    return {"ok": True, "items": items}

@app.get("/bedside/my")
async def get_my():
    owned = [t for t in state.商店列表 if t["id"] in state.owned_toys]
    return {"ok": True, "items": owned}

@app.post("/bedside/buy")
async def buy_toy(toy_id: str):
    if toy_id not in state.玩具配置:
        raise HTTPException(404, "玩具不存在")
    if toy_id in state.owned_toys:
        raise HTTPException(409, "已拥有")
    state.owned_toys.add(toy_id)
    state.add_murmur(f"购买了{toy_id}", source="shop", source_label="购入")
    return {"ok": True}

@app.post("/bedside/use/start")
async def start_toy(toy_id: str):
    if toy_id not in state.玩具配置:
        raise HTTPException(404, "玩具不存在")
    if toy_id not in state.owned_toys:
        raise HTTPException(403, "未拥有")
    if state.toy_active:
        raise HTTPException(409, "已有玩具使用中")
    state.toy_active = True
    state.toy_id = toy_id
    state.toy_name = state.玩具配置[toy_id]["name"]
    state.toy_stage = 1
    state.toy_desire = 0.0
    state.stamina = 100.0
    state.combo = None
    state.remote_paused = False
    state.remote_stim = 1.0
    state.add_murmur(f"开始使用{state.toy_name}", source="toy_start", source_label="开始")
    state.update()
    return {"ok": True}

@app.post("/bedside/use/next")
async def next_stage():
    if not state.toy_active:
        raise HTTPException(400, "未激活")
    if state.remote_paused:
        raise HTTPException(409, "已暂停")
    state.advance_toy()
    state.update()
    return {"ok": True, "stage": state.toy_stage, "desire": state.toy_desire, "stamina": state.stamina}

@app.get("/bedside/use/current")
async def current_toy():
    if not state.toy_active:
        return {"ok": True, "active": False}
    return {
        "ok": True,
        "active": True,
        "toy_id": state.toy_id,
        "toy_name": state.toy_name,
        "stage": state.toy_stage,
        "desire": state.toy_desire,
        "stamina": state.stamina
    }

@app.post("/bedside/use/edge")
async def edge():
    if not state.toy_active:
        raise HTTPException(400, "无激活玩具")
    state.add_murmur("边缘喊停！", source="edge", source_label="喊停")
    return {"ok": True}

@app.post("/bedside/use/position")
async def switch_position(position_id: str):
    if position_id not in state.positions:
        raise HTTPException(404, "体位不存在")
    old = state.current_position
    state.current_position = position_id
    state.add_murmur(f"切换体位：{old}→{position_id}", source="position", source_label="体位")
    return {"ok": True}

@app.get("/bedside/positions")
async def get_positions():
    items = [{"id": k, **v} for k, v in state.positions.items()]
    return {"ok": True, "items": items}

@app.get("/bedside/combos")
async def get_combos():
    return {"ok": True, "items": [{"id": "vibrator_oil", "name": "震动油", "effects": "触觉1.5x", "toys": ["vibrator", "oil"]}]}

# --- 遥控 ---
@app.post("/bedside/remote/stim")
async def remote_stim(mult: float):
    if not state.toy_active:
        raise HTTPException(400, "无激活玩具")
    state.remote_stim = max(0.3, min(2.5, mult))
    state.add_murmur(f"调档至{state.remote_stim:.1f}x", source="remote", source_label="调档")
    return {"ok": True, "stim": state.remote_stim}

@app.post("/bedside/remote/pause")
async def remote_pause():
    if not state.toy_active:
        raise HTTPException(400, "无激活玩具")
    state.remote_paused = True
    state.add_murmur("暂停", source="remote", source_label="暂停")
    return {"ok": True}

@app.post("/bedside/remote/resume")
async def remote_resume():
    if not state.toy_active:
        raise HTTPException(400, "无激活玩具")
    state.remote_paused = False
    state.add_murmur("恢复", source="remote", source_label="恢复")
    return {"ok": True}

@app.get("/bedside/remote/status")
async def remote_status():
    return {
        "ok": True,
        "toy_active": state.toy_active,
        "paused": state.remote_paused,
        "stim": state.remote_stim,
        "stage": state.toy_stage
    }

# --- 环境（原有） ---
@app.get("/bedside/env/shop")
async def env_shop():
    return {"ok": True, "items": [{"id": k, **v} for k, v in state.environments.items()]}

@app.post("/bedside/env/activate")
async def env_activate(env_id: str):
    if env_id not in state.environments:
        raise HTTPException(404, "环境不存在")
    state.active_env = env_id
    state.add_murmur(f"激活环境：{env_id}", source="env", source_label="环境")
    return {"ok": True}

@app.get("/bedside/env/active")
async def env_active():
    env = state.environments.get(state.active_env)
    return {"ok": True, "env": env}

@app.get("/bedside/env/evolution")
async def env_evolution():
    return {"ok": True, "items": []}

@app.get("/bedside/env/memory")
async def env_memory():
    return {"ok": True, "items": []}

@app.get("/bedside/env/seasonal")
async def env_seasonal():
    return {"ok": True, "items": []}

# ---------- 新增 API 路由（子系统） ----------
# --- 意淫 ---
@app.post("/fantasy/start")
async def fantasy_start(mode: str = "fantasy"):
    result = state.fantasy.start(mode)
    if result:
        state.add_murmur(f"意淫启动，模式：{mode}", source="fantasy", source_label="意淫")
        return {"ok": True, "stage": result}
    return {"ok": False, "error": "启动失败"}

@app.post("/fantasy/advance")
async def fantasy_advance():
    result = state.fantasy.advance()
    if result:
        state.add_murmur(f"意淫推进到阶段 {state.fantasy.current_stage}", source="fantasy", source_label="意淫")
        return {"ok": True, "stage": result}
    return {"ok": False, "error": "未启动"}

@app.post("/fantasy/stop")
async def fantasy_stop():
    state.fantasy.stop()
    state.add_murmur("意淫结束", source="fantasy", source_label="结束")
    return {"ok": True}

@app.get("/fantasy/status")
async def fantasy_status():
    return {"ok": True, "active": state.fantasy.active, "stage": state.fantasy.current_stage, "drive": state.fantasy.drive}

# --- 环境扩展 ---
@app.get("/bedside/env/list")
async def env_list():
    return {"ok": True, "environments": state.env.list_all()}

@app.post("/bedside/env/activate_ext")
async def env_activate_ext(env_id: str):
    if state.env.activate(env_id):
        state.add_murmur(f"环境切换（扩展）：{env_id}", source="env", source_label="环境")
        return {"ok": True}
    return {"ok": False, "error": "无效环境"}

@app.get("/bedside/env/active_ext")
async def env_active_ext():
    return {"ok": True, "active": state.env.get_active()}

@app.get("/bedside/env/evolution/{env_id}")
async def env_evolution_ext(env_id: str):
    tree = state.env.get_evolution_tree(env_id)
    if tree:
        return {"ok": True, "tree": tree}
    return {"ok": False, "error": "环境不存在"}

# --- 组合技 ---
@app.get("/bedside/combo/current")
async def combo_current():
    combo = state.combo.active_combo
    if combo:
        return {"ok": True, "combo": combo}
    return {"ok": True, "combo": None}

# --- 记忆回路 ---
@app.get("/memory/intimacy")
async def memory_intimacy():
    boost = state.memory.get_morning_boost()
    return {"ok": True, "morning_boost": boost, "last_intimacy": state.memory.last_intimacy_at}

@app.post("/memory/forge-filter")
async def forge_filter(text: str):
    filtered = state.memory.forge_filter(text)
    return {"ok": True, "filtered": filtered}

# ---------- 启动 ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)