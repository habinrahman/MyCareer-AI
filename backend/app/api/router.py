from fastapi import APIRouter

from app.api.routes import careers, chat, health, report, resume

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(resume.router)
api_router.include_router(chat.router)
api_router.include_router(report.router)
api_router.include_router(careers.router)
