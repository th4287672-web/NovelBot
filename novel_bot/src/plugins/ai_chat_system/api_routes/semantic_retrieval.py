# novel_bot/src/plugins/ai_chat_system/api_routes/semantic_retrieval.py

import asyncio
import logging
from typing import Dict, Any, List

import google.generativeai as genai
from google.generativeai import retriever
from fastapi import APIRouter, Body, HTTPException

# [核心修复] 将相对导入路径从 `.` 改为 `..`
from .. import global_state

logger = logging.getLogger("nonebot")
router = APIRouter(prefix="/semantic-retrieval", tags=["Semantic Retrieval"])

async def _create_or_update_corpus(user_id: str, world_data: Dict[str, Any]):
    """为单个世界书创建或更新云端Corpus。"""
    corpus_name = f"users/{user_id}/{world_data['name']}"
    logger.info(f"Syncing corpus: {corpus_name}")

    try:
        try:
            corpus = await asyncio.to_thread(genai.get_corpus, name=corpus_name)
            logger.info(f"Corpus '{corpus_name}' already exists. Updating...")
            existing_docs = await asyncio.to_thread(genai.list_documents, corpus_name=corpus.name)
            for doc in existing_docs:
                await asyncio.to_thread(genai.delete_document, name=doc.name)
            logger.info(f"Cleared existing documents in corpus '{corpus_name}'.")

        except Exception:
            logger.info(f"Corpus '{corpus_name}' not found. Creating new one...")
            corpus = await asyncio.to_thread(
                genai.create_corpus,
                name=corpus_name,
                display_name=world_data.get('displayName', world_data['name'])
            )

        if 'entries' in world_data and world_data['entries']:
            requests = []
            for entry in world_data['entries']:
                content = entry.get('content', '')
                keywords = ", ".join(entry.get('keywords', []))
                doc_id = entry.get('uid', f"doc_{hash(content)}")
                full_content = f"Keywords: {keywords}\n\nContent: {content}"

                requests.append(retriever.CreateDocumentRequest(
                    corpus=corpus.name,
                    document=retriever.Document(
                        display_name=entry.get('name', keywords[:30]),
                        custom_metadata={"keywords": keywords},
                        content=genai.types.Content(parts=[genai.types.Part(text=full_content)])
                    ),
                    document_id=doc_id
                ))
            
            if requests:
                logger.info(f"Batch creating {len(requests)} documents for corpus '{corpus.name}'...")
                await asyncio.to_thread(genai.batch_create_documents, requests=requests)
                logger.info("Batch creation complete.")

    except Exception as e:
        logger.error(f"Failed to process corpus '{corpus_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing corpus '{world_data['name']}': {e}")


@router.post("/sync-worlds")
async def sync_worlds_to_google_ai(payload: Dict = Body(...)):
    """接收多个世界书数据，并在Google AI上创建或更新对应的Corpora。"""
    user_id = payload.get("user_id")
    worlds: List[Dict] = payload.get("worlds")

    if not user_id or not worlds:
        raise HTTPException(status_code=400, detail="user_id and worlds are required.")

    api_manager = global_state.api_manager
    if not api_manager or not api_manager.keys:
        raise HTTPException(status_code=503, detail="API Manager not ready.")
    
    api_manager.configure_key(api_manager.last_successful_key_index)

    tasks = [_create_or_update_corpus(user_id, world) for world in worlds]
    
    try:
        await asyncio.gather(*tasks)
        return {"status": "success", "message": f"Successfully synced {len(worlds)} world books."}
    except HTTPException as e:
        raise e