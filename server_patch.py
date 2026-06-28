# ========== 追加到 server.py 末尾的新增 API 路由 ==========
# --- 意淫系统 ---
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
# --- 环境系统 ---
@app.get("/bedside/env/list")
async def env_list():
    return {"ok": True, "environments": state.env.list_all()}
@app.post("/bedside/env/activate")
async def env_activate(env_id: str):
    if state.env.activate(env_id):
        state.add_murmur(f"环境切换：{env_id}", source="env", source_label="环境")
        return {"ok": True}
    return {"ok": False, "error": "无效环境"}
@app.get("/bedside/env/active")
async def env_active():
    return {"ok": True, "active": state.env.get_active()}
@app.get("/bedside/env/evolution/{env_id}")
async def env_evolution(env_id: str):
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
