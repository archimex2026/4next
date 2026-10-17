import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import MEDIA_DIR, UPLOAD_DIR
from app.database import init_db
from app.services.demo_seeder import seed_demo_data
from app.routers import books, courses, lessons, flashcards, quizzes, demo, export

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and seed demo data
    print("Initializing Book2Course AI database...")
    init_db()
    try:
        seed_demo_data(generate_media_assets=True)
    except Exception as e:
        print(f"Startup seeder notice: {e}")
    yield
    print("Book2Course AI shutting down.")

app = FastAPI(
    title="Book2Course AI API",
    description="Transform any 100-1000+ page book into an interactive micro-learning course with lessons, audio, and video.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media static directory for audio & video streaming
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

# Include Routers
app.include_router(books.router)
app.include_router(courses.router)
app.include_router(lessons.router)
app.include_router(flashcards.router)
app.include_router(quizzes.router)
app.include_router(demo.router)
app.include_router(export.router)

@app.get("/")
def root():
    return {
        "app": "Book2Course AI",
        "tagline": "Turn a 300-page book into a 15-minute course.",
        "status": "ready",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
