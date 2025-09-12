# --- START OF FILE: novel_bot/src/plugins/ai_chat_system/music_service.py ---

import httpx
import asyncio
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import quote_plus
import os
import toml

logger = logging.getLogger("nonebot")

API_URL = "https://ts.lxmusic.tk/v2"
API_KEY = "lxmusic"
MUSIC_SOURCE_MAP = {
    "kw": "酷我音乐",
    "kg": "酷狗音乐",
    "tx": "QQ音乐",
    "wy": "网易云音乐",
    "mg": "咪咕音乐",
}


def _load_proxy_from_config() -> Optional[str]:
    try:
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "config.toml"
        )
        config_path = os.path.normpath(config_path)
        if not os.path.exists(config_path):
            return None
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = toml.load(f)
        proxy = config_data.get("ai_chat", {}).get("google_api_proxy", None)
        if proxy:
            logger.info(f"Music Service: Loaded proxy from config: {proxy}")
        return proxy
    except Exception as e:
        logger.error(f"Music Service: Failed to load proxy from config: {e}")
        return None


class MusicService:
    def __init__(self, proxy: Optional[str] = None):
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None

        self.client = httpx.AsyncClient(
            transport=transport,
            headers={
                "User-Agent": "lx-music-request/v2.5.0",
                "X-Request-Key": API_KEY,
            },
            timeout=20.0,
            follow_redirects=True,
        )

    async def _request(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0 and "data" in data:
                return data["data"]
            else:
                logger.error(
                    f"Music API Error: {data.get('msg', 'Unknown error')} for URL {url}"
                )
                return None
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Music API HTTP Error: {e.response.status_code} for URL {e.request.url}"
            )
            return None
        except httpx.ConnectError as e:
            logger.error(
                f"Music API Connect Error: Could not connect to {e.request.url}. Check your proxy/network settings."
            )
            return None
        except Exception as e:
            logger.error(f"Music API request failed for URL {url}: {e}", exc_info=True)
            return None

    async def search(
        self, keyword: str, page: int = 1, limit: int = 20
    ) -> List[Dict[str, Any]]:
        tasks = []
        for source in MUSIC_SOURCE_MAP.keys():
            url = (
                f"{API_URL}/{source}/music/search/{quote_plus(keyword)}/{page}/{limit}"
            )
            tasks.append(self._request(url))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_songs = []
        for i, res in enumerate(results):
            source_id = list(MUSIC_SOURCE_MAP.keys())[i]
            if isinstance(res, dict) and res.get("list"):
                for song in res["list"]:
                    song["source_id"] = source_id
                    song["source_name"] = MUSIC_SOURCE_MAP[source_id]
                    all_songs.append(song)
        return all_songs

    async def get_music_url(
        self, source: str, song_mid: str, quality: str = "320k"
    ) -> Optional[str]:
        url = f"{API_URL}/{source}/url/{song_mid}/{quality}"
        data = await self._request(url)
        return data if isinstance(data, str) else None

    async def get_lyric(self, source: str, song_mid: str) -> Optional[Dict[str, str]]:
        url = f"{API_URL}/{source}/lyric/{song_mid}"
        data = await self._request(url)
        return data if isinstance(data, dict) else None


music_service = MusicService(proxy=_load_proxy_from_config())
