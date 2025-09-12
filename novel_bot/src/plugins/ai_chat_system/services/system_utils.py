# novel_bot/src/plugins/ai_chat_system/services/system_utils.py

import os
import httpx
from typing import Dict, Any

async def check_network_connectivity(proxy_url: str | None = None) -> Dict[str, Any]:
    """
    检查到 Google 的网络连通性，并返回一个包含状态和消息的字典。
    现在可以接收一个临时的代理地址进行测试。
    """
    transport = httpx.AsyncHTTPTransport(proxy=proxy_url) if proxy_url else None
    
    try:
        async with httpx.AsyncClient(
            transport=transport, 
            follow_redirects=True, 
            timeout=20.0
        ) as client:
            response = await client.get("https://www.google.com")
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "message": f"✅ 网络检测成功！可以正常连接到Google (状态码: {response.status_code})。"
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ 网络检测失败，可以连接但状态码异常: {response.status_code}"
                }
    except httpx.TimeoutException:
        return {
            "success": False,
            "message": "❌ 网络检测超时！请检查代理服务器是否可用或超时设置。"
        }
    except httpx.ConnectError as e:
        return {
            "success": False,
            "message": f"❌ 网络检测连接失败！请检查代理地址和端口是否正确。\n错误: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 网络检测发生未知异常: {e}"
        }