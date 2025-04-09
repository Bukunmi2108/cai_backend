from fastapi import FastAPI
from .db import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth as auth_router, chat as chat_router, users as users_router, template as temp_router, category as category_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(users_router.router)
app.include_router(temp_router.router)
app.include_router(category_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
