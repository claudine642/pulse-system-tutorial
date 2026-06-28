# event_pool.py - 随机事件双池（内置+动态，后台自动补充）
import json
import os
import random
import threading
import time
class EventPool:
    def __init__(self, pool_file="data/life/random_events_pool.json"):
        self.pool_file = pool_file
        self.fallback_events = [
            "手机掉枕头底下震了一下",
            "窗没关严，一阵风灌进来，皮肤上的汗突然凉了",
            "润滑液顺着大腿根往下滴，痒的",
            "蜡烛突然跳了一下，影子晃了",
            "空调自动调低了温度，鸡皮疙瘩起来",
        ]
        self.dynamic_pool = []
        self.lock = threading.Lock()
        self.thread_running = False
        self._load_pool()
        self._start_refill_thread()
    def _load_pool(self):
        if os.path.exists(self.pool_file):
            try:
                with open(self.pool_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.dynamic_pool = data.get("events", [])
            except:
                self.dynamic_pool = []
        else:
            self.dynamic_pool = []
    def _save_pool(self):
        with open(self.pool_file, "w", encoding="utf-8") as f:
            json.dump({"events": self.dynamic_pool}, f, ensure_ascii=False, indent=2)
    def draw(self) -> str:
        with self.lock:
            if self.dynamic_pool:
                event = random.choice(self.dynamic_pool)
                self.dynamic_pool.remove(event)
                self._save_pool()
                return event
            else:
                return random.choice(self.fallback_events)
    def _refill(self):
        with self.lock:
            current = len(self.dynamic_pool)
            if current < 5:
                new_events = [f"模拟事件{i}: 身体忽然一颤，像被什么轻轻电了一下" for i in range(15 - current)]
                self.dynamic_pool.extend(new_events)
                self._save_pool()
    def _refill_loop(self):
        while self.thread_running:
            time.sleep(30)
            self._refill()
    def _start_refill_thread(self):
        self.thread_running = True
        thread = threading.Thread(target=self._refill_loop, daemon=True)
        thread.start()
    def stop(self):
        self.thread_running = False
