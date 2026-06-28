# mcp_pulse_server_http.py - 完整版（含玩具控制）

import asyncio
import json
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn
import mcp.types as types

# ---------- HTTP 客户端 ----------
import os
PULSE_API_BASE = os.environ.get("PULSE_API_BASE", "http://127.0.0.1:8000")

async def fetch_pulse_status() -> str:
    """获取身体状态"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{PULSE_API_BASE}/bedside/body-status")
            if resp.status_code == 200:
                data = resp.json()
                hr = data.get("heart_rate", {}).get("bpm", "--")
                temp = data.get("body_temperature", {}).get("celsius", "--")
                br = data.get("breathing", {}).get("rate", "--")
                depth = data.get("breathing", {}).get("depth", "--")
                chord = data.get("chord", "C6")
                toy_active = data.get("toy", {}).get("active", False)
                toy_name = data.get("toy", {}).get("toy_name", "无")
                stage = data.get("toy", {}).get("stage", 0)
                desire = data.get("toy", {}).get("desire_curve_pct", 0)
                stamina = data.get("toy", {}).get("stamina_pct", 100)
                senses = data.get("senses", {})
                touch = senses.get("touch", {}).get("value", 0)
                
                lines = [
                    f"【当前生命体征】",
                    f"心率：{hr} bpm",
                    f"体温：{temp} °C",
                    f"呼吸：{br} 次/分（{depth}）",
                    f"和弦：{chord}",
                    f"触觉：{round(touch, 2)}",
                ]
                if toy_active:
                    lines.append(f"【玩具状态】")
                    lines.append(f"正在使用：{toy_name}（阶段 {stage}/8）")
                    lines.append(f"欲望曲线：{desire}%")
                    lines.append(f"体力：{stamina}%")
                else:
                    lines.append("【玩具状态】未使用")
                
                return "\n".join(lines)
            else:
                return f"Pulse 后端返回错误：{resp.status_code}"
    except httpx.ConnectError:
        return "❌ 无法连接到 Pulse 后端，请确认 server.py 已启动（python server.py）"
    except Exception as e:
        return f"❌ 获取状态失败：{str(e)}"

# ---------- 玩具控制函数 ----------
async def pulse_buy_toy(toy_id: str) -> str:
    """购买玩具"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{PULSE_API_BASE}/bedside/buy", params={"toy_id": toy_id})
            if resp.status_code == 200:
                return f"✅ 已购买玩具：{toy_id}"
            else:
                return f"❌ 购买失败：{resp.json().get('detail', '未知错误')}"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"

async def pulse_start_toy(toy_id: str) -> str:
    """开始使用玩具"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{PULSE_API_BASE}/bedside/use/start", params={"toy_id": toy_id})
            if resp.status_code == 200:
                return f"✅ 已开始使用：{toy_id}，阶段 1/8"
            else:
                return f"❌ 启动失败：{resp.json().get('detail', '未知错误')}"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"

async def pulse_next_stage() -> str:
    """推进玩具阶段"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{PULSE_API_BASE}/bedside/use/next")
            if resp.status_code == 200:
                data = resp.json()
                return f"✅ 已推进：阶段 {data.get('stage')}/8，欲望 {data.get('desire', 0)*100:.1f}%，体力 {data.get('stamina', 0):.1f}%"
            else:
                return f"❌ 推进失败：{resp.json().get('detail', '未知错误')}"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"

async def pulse_switch_position(position_id: str) -> str:
    """切换体位"""
    valid_positions = ["sitting", "lying_back", "kneeling", "side_lying", "standing", "leaning"]
    if position_id not in valid_positions:
        return f"❌ 无效体位，可选：{', '.join(valid_positions)}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{PULSE_API_BASE}/bedside/use/position", params={"position_id": position_id})
            if resp.status_code == 200:
                return f"✅ 已切换体位：{position_id}"
            else:
                return f"❌ 切换失败：{resp.json().get('detail', '未知错误')}"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"

async def pulse_shop() -> str:
    """查看玩具商店"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{PULSE_API_BASE}/bedside/shop")
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                lines = ["【玩具商店】"]
                for item in items:
                    status = "✅ 已拥有" if item.get("owned") else "🔒 未购买"
                    lines.append(f"  {item['id']}：{item['name']}（{status}）")
                return "\n".join(lines)
            else:
                return f"❌ 获取商店失败：{resp.status_code}"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"

# ---------- MCP 服务器 ----------
app_server = Server("mcp-pulse")

@app_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_pulse",
            description="获取伴侣的实时身体状态，包括心率、体温、呼吸、和弦、五感、玩具使用进度等。",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="pulse_shop",
            description="查看玩具商店列表，显示所有可购买和已拥有的玩具。",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="pulse_buy_toy",
            description="购买指定玩具。参数：toy_id（玩具ID，如 vibrator、blindfold、ice 等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "toy_id": {"type": "string", "description": "玩具ID，如 vibrator、blindfold、ice、cup、ring、massager、feather、oil、clamp、warm_liquid"}
                },
                "required": ["toy_id"]
            },
        ),
        types.Tool(
            name="pulse_start_toy",
            description="开始使用已购买的玩具。参数：toy_id（玩具ID）",
            inputSchema={
                "type": "object",
                "properties": {
                    "toy_id": {"type": "string", "description": "已购买的玩具ID"}
                },
                "required": ["toy_id"]
            },
        ),
        types.Tool(
            name="pulse_next_stage",
            description="推进玩具使用阶段（共8阶段，从接触→加速→高峰前→沉浸→失控→边缘→峰值）。连续调用会让身体反应逐渐增强。",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="pulse_switch_position",
            description="切换体位，影响体力消耗和身体感受。可选：sitting（坐着）、lying_back（躺着）、kneeling（跪趴）、side_lying（侧躺）、standing（站着）、leaning（靠坐）",
            inputSchema={
                "type": "object",
                "properties": {
                    "position_id": {"type": "string", "description": "体位ID，可选：sitting、lying_back、kneeling、side_lying、standing、leaning"}
                },
                "required": ["position_id"]
            },
        ),
    ]

@app_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_pulse":
        result = await fetch_pulse_status()
        return [types.TextContent(type="text", text=result)]
    elif name == "pulse_shop":
        result = await pulse_shop()
        return [types.TextContent(type="text", text=result)]
    elif name == "pulse_buy_toy":
        toy_id = arguments.get("toy_id")
        if not toy_id:
            return [types.TextContent(type="text", text="❌ 缺少参数：toy_id")]
        result = await pulse_buy_toy(toy_id)
        return [types.TextContent(type="text", text=result)]
    elif name == "pulse_start_toy":
        toy_id = arguments.get("toy_id")
        if not toy_id:
            return [types.TextContent(type="text", text="❌ 缺少参数：toy_id")]
        result = await pulse_start_toy(toy_id)
        return [types.TextContent(type="text", text=result)]
    elif name == "pulse_next_stage":
        result = await pulse_next_stage()
        return [types.TextContent(type="text", text=result)]
    elif name == "pulse_switch_position":
        position_id = arguments.get("position_id")
        if not position_id:
            return [types.TextContent(type="text", text="❌ 缺少参数：position_id")]
        result = await pulse_switch_position(position_id)
        return [types.TextContent(type="text", text=result)]
    else:
        raise ValueError(f"未知工具: {name}")

# ---------- HTTP 服务 ----------
sse = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app_server.run(
            streams[0], streams[1], app_server.create_initialization_options()
        )

starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/mcp", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    uvicorn.run(starlette_app, host="0.0.0.0", port=8001)