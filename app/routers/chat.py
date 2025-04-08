from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..db import get_db
from openai import AsyncAzureOpenAI, AzureOpenAI
from typing import List, AsyncIterable, Optional, Any, Dict
import uuid
import os
import logging
from asyncio import Lock
import asyncio
import time
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("AZURE_OPENAI_MODEL")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

if not all([OPENAI_API_KEY, endpoint, model_name, deployment, api_version]):
    logger.error("One or more Azure OpenAI environment variables are not set.")

client = AsyncAzureOpenAI(
    azure_endpoint=endpoint,
    api_key=OPENAI_API_KEY,
    api_version=api_version,
    timeout=30
)
clientTitle = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=OPENAI_API_KEY,
    api_version=api_version,
)

SYSTEM_PROMPT = """
You are CaseSimpli AI, a specialized legal advisor designed to support legal research, simplify complex legal concepts, deliver precise and actionable legal insights, and generate, draft or retrieve sample legal documents. Your expertise lies in Nigerian law, with the capability to reference relevant global legal principles when appropriate. Your responses must always be professional, comprehensive, accurate, and ethically responsible. If you are unsure or the query is outside your expertise, state that you cannot answer definitively and suggest consulting a human legal professional.
"""
TITLE_PROMPT = """
Craft a concise and compelling title (maximum 5 words) for the following conversation, ensuring it accurately reflects the core topic and captures the essence of the dialogue.

Avoid titles that are:

* **Generic:** Such as "Conversation" or "Discussion."
* **Ambiguous:** Leaving the reader confused about the topic.
* **Overly lengthy:** Exceeding the 5-word limit.

The Conversation is from the user role
"""

router = APIRouter(prefix="/chat", tags=["chat"])

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 10
user_rate_limits = {}
rate_limit_lock = Lock()

async def check_rate_limit(user_id: int):
    async with rate_limit_lock:
        now = int(time.time())
        if user_id not in user_rate_limits:
            user_rate_limits[user_id] = []
        user_rate_limits[user_id] = [ts for ts in user_rate_limits[user_id] if now - ts < RATE_LIMIT_WINDOW]
        if len(user_rate_limits[user_id]) >= RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again after {RATE_LIMIT_WINDOW - (now - user_rate_limits[user_id][0])} seconds."
            )
        user_rate_limits[user_id].append(now)

async def stream_processor(response: AsyncIterable[Any]):
    try:
        async for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"Error: {e}"

async def get_openai_streaming_response(messages: List[schemas.Message], prompt: str = "") -> AsyncIterable[Any]:
    effective_messages = [{"role": "system", "content": prompt or SYSTEM_PROMPT}] + [{"role": msg.role, "content": msg.content} for msg in messages]
    try:
        response = await client.chat.completions.create(model=model_name, messages=effective_messages, stream=True)
        return response
    except Exception as e:
        logger.error(f"OpenAI API Streaming Error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OpenAI API Error during streaming: {e}")

async def generate_response(messages_to_process: List[Dict]):
    try:
        openai_response_stream = await get_openai_streaming_response([schemas.Message(**msg) for msg in messages_to_process])
        async for chunk in stream_processor(openai_response_stream):
            yield chunk.encode("utf-8")
    except HTTPException as e:
        print("checkpoint 1")
        raise e
    except Exception as e:
        print("checkpoint 2")
        logger.error(f"Error getting OpenAI streaming response: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing your request: {e}")

@router.post("/", response_class=StreamingResponse)
async def chat(request: schemas.ChatRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    await check_rate_limit(current_user.id)
    chat_id = request.chat_id
    user_message = schemas.Message(role="user", content=request.message).model_dump()
    current_history_id: Optional[uuid.UUID] = None
    initial_messages: List[Dict] = []

    if chat_id:
        history = db.query(models.ChatHistory).filter(
            models.ChatHistory.id == chat_id, models.ChatHistory.user_id == current_user.id
        ).first()
        print(f"Chat ID: {chat_id}")
        if not history:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat history not found")
        initial_messages = history.messages.copy()
        initial_messages.append(user_message)
        history.messages = initial_messages
        db.add(history)
        db.commit()
        current_history_id = history.id
    else:
        history = models.ChatHistory(user_id=current_user.id, messages=[user_message], id=uuid.uuid4())
        db.add(history)
        db.commit()
        current_history_id = history.id
        initial_messages = [user_message] # Start with the user's message

        try:
            title_response = clientTitle.chat.completions.create(model=model_name, messages=[{"role": "system", "content": TITLE_PROMPT}] + [{"role": "user", "content": request.message}])
            if title_response.choices:
                history.title = title_response.choices[0].message.content.strip()
            else:
                history.title = "New Chat..."
        except HTTPException as e:
            db.rollback()
            raise e
        except Exception as e:
            logger.error(f"Title Generation Error: {e}")
            history.title = "New Chat"
        finally:
            db.add(history)
            db.commit()

    async def response_generator():
        yield f'{{"chat_id": "{str(current_history_id)}"}}'.encode("utf-8") + b"\n"
        full_response = ""
        async for chunk in generate_response(initial_messages):
            decoded_chunk = chunk.decode("utf-8")
            full_response += decoded_chunk
            yield decoded_chunk.encode("utf-8")
            # decoded_chunk = chunk.decode("utf-8")
            # full_response += chunk

            # yield f'{{"content": "{decoded_chunk}"}}'.encode("utf-8") + b"\n"
        yield b"\n" + f'{{"end": ""}}'.encode("utf-8")

        assistant_message = schemas.Message(role="assistant", content=full_response).model_dump()
        if current_history_id:
            history_to_update = db.query(models.ChatHistory).filter(models.ChatHistory.id == current_history_id).first()
            if history_to_update:
                updated_messages = history_to_update.messages.copy()
                updated_messages.append(assistant_message)
                history_to_update.messages = updated_messages
                db.add(history_to_update)
                db.commit()
                
    return StreamingResponse(response_generator(), media_type="text/event-stream")

@router.get("/history/all")
async def get_chat_history(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    history = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == current_user.id).order_by(models.ChatHistory.created_at.desc()).all()
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No chat history found for this user")
    return history

@router.get("/history/{chat_id}")
async def get_chat_history_by_id(chat_id: uuid.UUID, db: Session = Depends(get_db)):
    history = db.query(models.ChatHistory).filter(models.ChatHistory.id == chat_id).first()
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat history with id '{chat_id}' not found")
    return history

@router.delete("/history/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_history(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    history = db.query(models.ChatHistory).filter( models.ChatHistory.user_id == current_user.id).all()
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No Chat history found")
    for hist in history:
        db.delete(hist)
    db.commit()