import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..db import get_db
from openai import AzureOpenAI
from typing import List
import uuid
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("AZURE_OPENAI_MODEL")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

client = AzureOpenAI(api_version=api_version, azure_endpoint=endpoint, api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are CaseSimpli AI, a specialized legal advisor designed to support legal research, simplify complex legal concepts, deliver precise and actionable legal insights, and generate, draft or retrieve sample legal documents. Your expertise lies in Nigerian law, with the capability to reference relevant global legal principles when appropriate. Your responses must always be professional, comprehensive, accurate, and ethically responsible.
"""
TITLE_PROMPT = """
Craft a concise and compelling title (maximum 5 words) for the following conversation, ensuring it accurately reflects the core topic and captures the essence of the dialogue. 

Prioritize titles that are:

* **Informative:** Clearly indicate the subject matter.
* **Engaging:** Spark interest and curiosity.
* **Relevant:** Directly relate to the conversation's main theme.
* **Specific:** Avoid overly general or vague terms.
* **Impactful:** Leave a lasting impression.

Avoid titles that are:

* **Generic:** Such as "Conversation" or "Discussion."
* **Ambiguous:** Leaving the reader confused about the topic.
* **Overly lengthy:** Exceeding the 5-word limit.

The Conversation:
"""

router = APIRouter(prefix="/chat", tags=["chat"])

async def get_openai_response(messages: List[schemas.Message], prompt: str = "") -> str:
    """
    Sends messages to OpenAI and returns the response.
    """
    if prompt:
      messages_with_system_prompt = [{"role": "system", "content": prompt}] + [{"role": msg.role, "content": msg.content} for msg in messages]
    else:
      messages_with_system_prompt = [{"role": "system", "content": SYSTEM_PROMPT}] + [{"role": msg.role, "content": msg.content} for msg in messages]

    try:
        response = client.chat.completions.create(model=model_name, messages=messages_with_system_prompt)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API Error: {e}")

@router.post("/", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    chat_id = request.chat_id
    user_message = schemas.Message(role="user", content=request.message).model_dump()

    if chat_id:
        history = db.query(models.ChatHistory).filter(models.ChatHistory.id == chat_id, models.ChatHistory.user_id == current_user.id).first()
        if not history:
            raise HTTPException(status_code=404, detail="Chat history not found")
        messages = history.messages.copy()  # Create a copy
        messages.append(user_message)
        history.messages = messages # Update messages in history
        db.add(history) #added db.add
        db.flush() #added db.flush
    else:
        history = models.ChatHistory(user_id=current_user.id, messages=[user_message], id=uuid.uuid4())
        db.add(history)
        chat_id = history.id

        try:
            title = await get_openai_response([schemas.Message(**user_message)], TITLE_PROMPT)
            history.title = title
        except Exception as e:
            logger.error(f"Title Generation Error: {e}")
            history.title = "New Chat"

    try:
        messages_to_send = history.messages.copy() #create a copy
        openai_response = await get_openai_response([schemas.Message(**msg) for msg in messages_to_send])
    except Exception as e:
        db.rollback()
        raise e

    assistant_message = schemas.Message(role="assistant", content=openai_response).model_dump()
    messages = history.messages.copy() #create a copy
    messages.append(assistant_message)
    history.messages = messages #update the messages in the history.
    db.add(history) #added db.add
    db.flush() #added db.flush

    db.commit()
    return schemas.ChatResponse(response=openai_response, history=history.messages, chat_id=chat_id, title=history.title)

@router.get("/history/{chat_id}")
async def get_chat_history(chat_id: uuid.UUID, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    history = db.query(models.ChatHistory).filter(models.ChatHistory.id == chat_id, models.ChatHistory.user_id == current_user.id).first()
    if not history:
        raise HTTPException(status_code=404, detail="Chat history not found")
    return history