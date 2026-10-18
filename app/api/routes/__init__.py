from fastapi import APIRouter

from app.api.routes.audiobookshelf import router as audiobookshelf_router
from app.api.routes.authors import router as authors_router
from app.api.routes.books import router as books_router
from app.api.routes.integration import router as integration_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.ui import router as ui_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(authors_router)
api_router.include_router(books_router)
api_router.include_router(audiobookshelf_router)
api_router.include_router(recommendations_router)
api_router.include_router(integration_router)
api_router.include_router(ui_router)
