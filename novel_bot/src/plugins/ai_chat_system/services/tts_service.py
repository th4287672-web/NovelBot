# novel_bot/src/plugins/ai_chat_system/services/tts_service.py

import httpx
import hmac
import hashlib
import base64
import uuid
import json
import os
import toml
from datetime import datetime, timezone
from email.utils import formatdate
from urllib.parse import quote, urlencode
from typing import Optional, Dict, List, Any
import logging
import asyncio
import edge_tts # [新增]

from .. import global_state
from .tts_merger import wav_base64_to_mp3_bytes

logger = logging.getLogger("nonebot")

# --- Microsoft TTS 实现 ---
class MicrosoftTTS:
    def __init__(self, client: httpx.AsyncClient):
        self.endpoint_url = "https://dev.microsofttranslator.com/apps/endpoint?api-version=1.0"
        self.voices_url = "https://eastus.api.speech.microsoft.com/cognitiveservices/voices/list"
        self.client = client
        self.endpoint_info: Dict[str, Any] = {}
        self.voices: List[Dict[str, Any]] = []

    async def _get_sign(self) -> str:
        url_to_sign = self.endpoint_url.split("://")[1]
        encoded_url = quote(url_to_sign, safe="")
        request_uuid = uuid.uuid4().hex
        formatted_date = formatdate(timeval=None, localtime=False, usegmt=True).lower()
        string_to_sign = f"MSTranslatorAndroidApp{encoded_url}{formatted_date}{request_uuid}".lower()
        secret_key = base64.b64decode("oik6PdDdMnOXemTbwvMn9de/h9lFnfBaCWbGMMZqqoSaQaqUOqjVGm5NqsmjcBI1x+sS9ugjB55HEJWRiFXYFw==")
        mac = hmac.new(secret_key, string_to_sign.encode("utf-8"), hashlib.sha256)
        return f"MSTranslatorAndroidApp::{base64.b64encode(mac.digest()).decode('utf-8')}::{formatted_date}::{request_uuid}"

    async def _get_endpoint(self):
        logger.info("[INFO] TTS: Requesting new Microsoft endpoint info...")
        signature = await self._get_sign()
        
        # [核心修复] 严格遵循 test_tts_auth.py 中验证成功的请求头
        headers = {
            "Accept-Language": "zh-Hans",
            "X-ClientVersion": "4.0.530a 5fe1dc6c",
            "X-UserId": "0f04d16a175c411e",
            "X-HomeGeographicRegion": "zh-Hans-CN",
            "X-ClientTraceId": uuid.uuid4().hex,
            "X-MT-Signature": signature,
            "User-Agent": "okhttp/4.5.0",
            "Content-Type": "application/json; charset=utf-8",
            "Accept-Encoding": "gzip",
        }
        
        # 直接使用 self.client，它的代理已在 TtsServiceManager 中正确配置
        response = await self.client.post(self.endpoint_url, headers=headers, content="")
        response.raise_for_status()
        self.endpoint_info = response.json()
            
        logger.info(f"[SUCCESS] TTS: Got new Microsoft endpoint for region: {self.endpoint_info.get('r')}")

    async def get_voices(self, force_refresh: bool = False) -> list:
        if self.voices and not force_refresh: return self.voices
        logger.info("[INFO] TTS: Fetching available voices from Microsoft API...")
        try:
            headers = { "Origin": "https://azure.microsoft.com", "Referer": "https://azure.microsoft.com" }
            response = await self.client.get(self.voices_url, headers=headers)
            response.raise_for_status()
            self.voices = response.json()
            return [{
                "DisplayName": v.get("DisplayName"), "ShortName": v.get("ShortName"), "Gender": v.get("Gender"), "Provider": "Microsoft"
            } for v in self.voices if v.get("Locale") == "zh-CN" and "Neural" in v.get("VoiceType", "")]
        except Exception as e:
            logger.error(f"[ERROR] TTS: Failed to fetch Microsoft voices: {e}")
            return []

    async def get_audio(self, text: str, voice_name: str, rate: int, volume: int, pitch: int) -> bytes:
        if not self.endpoint_info or "t" not in self.endpoint_info: await self._get_endpoint()
        rate_val, pitch_val = rate - 50, pitch - 50
        ssml = (
            f'<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" version="1.0" xml:lang="zh-CN">'
            f'<voice name="{voice_name}"><prosody rate="{rate_val}%" pitch="{pitch_val}%" volume="{volume}">{text}</prosody></voice></speak>'
        )
        region, token = self.endpoint_info["r"], self.endpoint_info["t"]
        tts_url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        headers = { "Authorization": token, "Content-Type": "application/ssml+xml", "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3" }
        try:
            response = await self.client.post(tts_url, content=ssml.encode("utf-8"), headers=headers)
            if response.status_code == 401:
                await self._get_endpoint()
                headers["Authorization"] = self.endpoint_info["t"]
                response = await self.client.post(tts_url, content=ssml.encode("utf-8"), headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"[ERROR] TTS: Failed to get Microsoft audio: {e}")
            raise

# [新增] Edge TTS 实现
class EdgeTTS:
    def __init__(self, proxy: str = None):
        self.proxy = proxy
        self.voices: List[Dict[str, Any]] = []
    
    async def get_voices(self, force_refresh: bool = False) -> list:
        if self.voices and not force_refresh: return self.voices
        logger.info("[INFO] TTS: Fetching available voices from Edge TTS...")
        try:
            voices_list = await edge_tts.list_voices()
            self.voices = [{
                "DisplayName": v['FriendlyName'], "ShortName": v['Name'], "Gender": v['Gender'], "Provider": "Edge"
            } for v in voices_list if v['Locale'] == 'zh-CN']
            return self.voices
        except Exception as e:
            logger.error(f"[ERROR] TTS: Failed to fetch Edge voices: {e}")
            return []

    async def get_audio(self, text: str, voice_name: str, rate: int, volume: int, pitch: int) -> bytes:
        rate_str = f"{'+' if rate >= 50 else ''}{(rate - 50) * 2}%"
        volume_str = f"{'+' if volume >= 50 else ''}{(volume - 50) * 2}%"
        pitch_str = f"{'+' if pitch >= 50 else ''}{pitch - 50}Hz"
        
        communicate = edge_tts.Communicate(text, voice_name, rate=rate_str, volume=volume_str, pitch=pitch_str, proxy=self.proxy)
        audio_bytes = b""
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            return audio_bytes
        except Exception as e:
            logger.error(f"[ERROR] TTS: Failed to get Edge audio: {e}")
            raise

# [新增] ChatTTS API 实现
class ChatTTS:
    def __init__(self, api_url: str, proxy: str = None):
        self.api_url = api_url.rstrip('/')
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
        self.client = httpx.AsyncClient(transport=transport, timeout=120.0)
        self.voices = [
            {"DisplayName": "默认音色 (Seed 42)", "ShortName": "42", "Gender": "Unknown", "Provider": "ChatTTS"},
            {"DisplayName": "音色 2 (Seed 1024)", "ShortName": "1024", "Gender": "Unknown", "Provider": "ChatTTS"},
            {"DisplayName": "音色 3 (Seed 2048)", "ShortName": "2048", "Gender": "Unknown", "Provider": "ChatTTS"},
        ]

    async def get_voices(self, force_refresh: bool = False) -> list:
        return self.voices

    async def get_audio(self, text: str, voice_name: str, rate: int, volume: int, pitch: int) -> bytes:
        payload = { "text": text, "seed": int(voice_name) }
        try:
            response = await self.client.post(f"{self.api_url}/tts", json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("audio_b64"):
                return await asyncio.to_thread(wav_base64_to_mp3_bytes, data["audio_b64"])
            raise ValueError("ChatTTS API did not return audio data.")
        except httpx.ConnectError:
            logger.error(f"[ERROR] TTS: Could not connect to ChatTTS API at {self.api_url}. Is the service running?")
            raise
        except Exception as e:
            logger.error(f"[ERROR] TTS: Failed to get ChatTTS audio: {e}")
            raise
            
# [新增] Hugging Face Inference API (for Qwen-Audio)
class HuggingFaceTTS:
    def __init__(self, api_key: str, model_id: str, proxy: str = None):
        self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
        self.client = httpx.AsyncClient(transport=transport, timeout=120.0)
        self.voices = [
            {"DisplayName": "Qwen-Audio", "ShortName": model_id, "Gender": "Unknown", "Provider": "HuggingFace"}
        ]

    async def get_voices(self, force_refresh: bool = False) -> list:
        return self.voices
    
    async def get_audio(self, text: str, voice_name: str, rate: int, volume: int, pitch: int) -> bytes:
        payload = {"inputs": text}
        try:
            response = await self.client.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            # HF API returns raw audio bytes, which might not be mp3.
            # We assume it's a format ffmpeg can handle and convert it.
            from .tts_merger import _run_ffmpeg
            return await asyncio.to_thread(_run_ffmpeg, response.content, 'wav', 'mp3')
        except Exception as e:
            logger.error(f"[ERROR] TTS: Failed to get HuggingFace audio: {e}")
            raise

def _load_proxy_from_config() -> Optional[str]:
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.toml")
        config_path = os.path.normpath(config_path)
        if not os.path.exists(config_path): return None
        with open(config_path, "r", encoding="utf-8") as f: config_data = toml.load(f)
        return config_data.get("ai_chat", {}).get("google_api_proxy", None)
    except Exception: return None

class TtsServiceManager:
    def __init__(self, proxy: Optional[str]):
        # [核心修复] 使用更可靠的 transport 方式来配置代理
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
        
        # 创建一个不带任何默认头的干净 client
        clean_client = httpx.AsyncClient(transport=transport, timeout=60.0)
        
        # [新增] 加载新服务的配置
        tts_service_config = {}
        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.toml")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = toml.load(f)
                tts_service_config = config_data.get("tts_services", {})
        except Exception as e:
            logger.warning(f"Could not load tts_services config: {e}")
            
        chat_tts_url = tts_service_config.get("chat_tts_api_url", "http://127.0.0.1:9966")
        hf_api_key = tts_service_config.get("huggingface_api_key")
        qwen_model_id = tts_service_config.get("qwen_tts_model_id", "Qwen/Qwen-Audio")

        self.services: Dict[str, Any] = {
            "microsoft": MicrosoftTTS(clean_client),
            "edge": EdgeTTS(proxy),
            "chat_tts": ChatTTS(api_url=chat_tts_url, proxy=proxy),
            "huggingface": HuggingFaceTTS(api_key=hf_api_key, model_id=qwen_model_id, proxy=proxy),
        }

    def get_service_for_voice(self, voice_name: str) -> Optional[Any]:
        for service in self.services.values():
            if hasattr(service, 'voices') and service.voices:
                for voice in service.voices:
                    if voice["ShortName"] == voice_name:
                        return service
        return None

    async def get_voices(self, force_refresh: bool = False) -> list:
        all_voices = []
        tasks = [service.get_voices(force_refresh) for service in self.services.values()]
        results = await asyncio.gather(*tasks)
        for result in results:
            all_voices.extend(result)
        return all_voices
    
    async def get_audio(self, user_id: str, text: str, voice_name: str, rate: int, volume: int, pitch: int) -> bytes:
        service = self.get_service_for_voice(voice_name)
        if not service:
             # Fallback to user's configured service if voice not found
            if global_state.data_manager:
                user_config = global_state.data_manager.get_user_config(user_id)
                service_name = user_config.get("tts_service_config", {}).get("service", "microsoft")
                service = self.services.get(service_name)
        
        if not service:
            raise ValueError(f"No TTS service found for voice '{voice_name}' or configured default.")
            
        return await service.get_audio(text, voice_name, rate, volume, pitch)

tts_client = TtsServiceManager(proxy=_load_proxy_from_config())