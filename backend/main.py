import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.models import init_db
from api.promotions import router as promotions_router
from api.analytics import router as analytics_router
from api.scraping import router as scraping_router
from api.review import router as review_router


# [FIX] Replace deprecated @app.on_event("startup") with lifespan context manager
@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="Ecom-Watch", version="0.2.0", lifespan=lifespan)

# [FIX] CORS: restrict origins instead of wildcard; disable credentials with wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(promotions_router)
app.include_router(analytics_router)
app.include_router(scraping_router)
app.include_router(review_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
