# novel_bot/src/plugins/ai_chat_system/services/tts_merger.py

import asyncio
import wave
from io import BytesIO
from typing import List, Tuple, Any, Optional
from nonebot import logger
import base64
import subprocess
import sys

from ..services.task_manager import TaskManager

CHANNELS = 1
SAMPWIDTH = 2
FRAMERATE = 24000

def _run_ffmpeg(input_bytes: bytes, input_format: str, output_format: str, extra_args: List[str] = []) -> bytes:
    command = [
        'ffmpeg',
        '-f', input_format,
        '-i', 'pipe:0',
        *extra_args,
        '-f', output_format,
        '-'
    ]
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        output_bytes, stderr = process.communicate(input=input_bytes)
        if process.returncode != 0:
            error_message = stderr.decode('utf-8', errors='ignore')
            logger.error(f"FFmpeg ({input_format} -> {output_format}) failed: {error_message}")
            raise RuntimeError(f"FFmpeg conversion failed: {error_message}")
        return output_bytes
    except FileNotFoundError:
        logger.critical("FATAL: `ffmpeg` command not found. Please install FFmpeg and ensure it's in your system's PATH.")
        raise RuntimeError("FFmpeg is not installed or not in PATH.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during FFmpeg conversion: {e}")
        raise

def mp3_bytes_to_wav_data(mp3_bytes: bytes) -> bytes:
    return _run_ffmpeg(mp3_bytes, 'mp3', 's16le', ['-ac', str(CHANNELS), '-ar', str(FRAMERATE)])

def wav_base64_to_mp3_bytes(b64_string: str) -> bytes:
    wav_bytes = base64.b64decode(b64_string.split(",", 1)[1])
    return _run_ffmpeg(wav_bytes, 'wav', 'mp3', ['-b:a', '48k'])

def webm_base64_to_mp3_bytes(b64_string: str) -> bytes:
    webm_bytes = base64.b64decode(b64_string)
    return _run_ffmpeg(webm_bytes, 'webm', 'mp3', ['-b:a', '48k'])

async def synthesize_and_merge_audio(
    user_id: str, 
    segments: List[Tuple[str, str]], 
    rate: int = 50, 
    volume: int = 50, 
    pitch: int = 50,
    task_id: Optional[str] = None,
    task_manager_instance: Optional[TaskManager] = None
) -> bytes:
    from ..services.tts_service import tts_client

    async def get_segment_audio_data(text: str, voice: str) -> bytes:
        try:
            mp3_bytes = await tts_client.get_audio(user_id, text, voice, rate, volume, pitch)
            return await asyncio.to_thread(mp3_bytes_to_wav_data, mp3_bytes)
        except Exception as e:
            logger.error(f"TTS Merger: Failed to synthesize or convert segment with voice {voice}: {e}")
            return b'\x00' * (SAMPWIDTH * FRAMERATE // 5)

    tasks = []
    for i, (text, voice) in enumerate(segments):
        tasks.append(get_segment_audio_data(text, voice))
    
    logger.info(f"TTS Merger: Starting batch synthesis for {len(tasks)} segments...")
    
    audio_data_list = []
    for i, f in enumerate(asyncio.as_completed(tasks)):
        audio_data_list.append(await f)
        if task_id and task_manager_instance:
            progress = 20 + int(((i + 1) / len(tasks)) * 55)
            await task_manager_instance.update_task_progress(task_id, progress, f"正在合成第 {i+1}/{len(tasks)} 段音频")

    combined_wav_data = b"".join(audio_data_list)
    
    output_wav_buffer = BytesIO()
    with wave.open(output_wav_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPWIDTH)
        wf.setframerate(FRAMERATE)
        wf.writeframes(combined_wav_data)
    output_wav_buffer.seek(0)
    
    if task_id and task_manager_instance: await task_manager_instance.update_task_progress(task_id, 85, "合并音频中")
    mp3_output = _run_ffmpeg(output_wav_buffer.getvalue(), 'wav', 'mp3', ['-b:a', '48k'])
    
    logger.info("TTS Merger: Batch synthesis and merging complete.")
    return mp3_output