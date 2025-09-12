# novel_bot/src/plugins/ai_chat_system/api_routes/music.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..music_service import music_service

# [核心修正] 移除冗余的 prefix="/api"
router = APIRouter(prefix="/music", tags=["Music"])


@router.get("/search")
async def search_music(keyword: str, page: int = 1, limit: int = 20):
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required.")
    try:
        results = await music_service.search(keyword, page, limit)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/url")
async def get_music_url(source: str, song_mid: str, quality: Optional[str] = "320k"):
    try:
        url = await music_service.get_music_url(source, song_mid, quality)
        if url:
            return {"status": "success", "data": url}
        else:
            raise HTTPException(
                status_code=404, detail="Music URL not found or API error."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lyric")
async def get_music_lyric(source: str, song_mid: str):
    try:
        lyric_data = await music_service.get_lyric(source, song_mid)
        if lyric_data:
            return {"status": "success", "data": lyric_data}
        else:
            raise HTTPException(status_code=404, detail="Lyric not found or API error.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))