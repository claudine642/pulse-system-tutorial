# mcp_pulse_server_http.py
# 将 Pulse REST API 包装成 MCP over HTTP 服务

import asyncio
import json
import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn
import mcp.types as types

# ---------- HTTP 客户端（与之前相同） ----------
PULSE_API_BASE = "http://127.0.0.1:8000"

async def fetch_pulse_status() -> str:
    """从 Pulse 后端拉取身体状态"""
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
                
                lines = [
                    f"【当前生命体征】",
                    f"心率：{hr} bpm",
                    f"体温：{temp} °C",
                    f"呼吸：{br} 次/分（{depth}）",
                    f"和弦：{chord}",
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

# ---------- MCP 服务器（核心逻辑与之前相同） ----------
app_server = Server("mcp-pulse")

@app_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_pulse",
            description="获取伴侣的实时身体状态，包括心率、体温、呼吸、和弦，以及玩具使用进度（如有）。用于在对话前注入身体感知上下文。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    ]

@app_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_pulse":
        result = await fetch_pulse_status()
        return [types.TextContent(type="text", text=result)]
    raise ValueError(f"未知工具: {name}")

# ---------- 启动 HTTP 服务（新增部分） ----------
# 创建 SSE 传输层
sse = SseServerTransport("/messages/")

async def handle_sse(request):
    """处理 SSE 连接"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app_server.run(
            streams[0], streams[1], app_server.create_initialization_options()
        )

# 创建 Starlette 应用
starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/mcp", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    # 监听所有网络接口，端口 8001
    uvicorn.run(starlette_app, host="0.0.0.0", port=8001)