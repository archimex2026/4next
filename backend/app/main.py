import re
from contextlib import asynccontextmanager, closing
from urllib.parse import urlsplit
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from app.config import ALLOWED_ORIGINS, MEDIA_DIR
from app.database import get_db_connection, init_db
from app.security import check_course_access, optional_user
from app.request_limits import RequestBodyLimitsMiddleware
from app.services.demo_seeder import seed_demo_data
from app.routers import auth, books, community, courses, lessons, flashcards, quizzes, demo, export, groups, study


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_demo_data(generate_media_assets=False)
    yield


app = FastAPI(title="4Next API",description="Materiale de studiu, practică și explicații bazate pe documentele tale.",version="2.0.0",lifespan=lifespan)
app.add_middleware(RequestBodyLimitsMiddleware)
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_credentials=True,
    allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"],allow_headers=["Content-Type","Accept"])


@app.middleware("http")
async def protect_browser_requests(request: Request,call_next):
    if request.method not in ("GET","HEAD","OPTIONS"):
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        if not origin and referer:
            parsed = urlsplit(referer)
            origin = f"{parsed.scheme}://{parsed.netloc}"
        if (origin and origin.rstrip("/") not in ALLOWED_ORIGINS) or request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail":"Originea solicitării nu este permisă."},status_code=403)
    response = await call_next(request)
    if request.url.path.startswith(("/api/","/media/")):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = ", ".join(filter(None,[response.headers.get("Vary"),"Cookie"]))
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/media/{media_path:path}",include_in_schema=False)
def protected_media(media_path: str,user: dict | None=Depends(optional_user)):
    if not re.fullmatch(r"(?:audio|video|diagrams)/[A-Za-z0-9_-]+\.(?:mp3|mp4|png|svg|jpg|webp)",media_path):
        raise HTTPException(404,"Fișierul nu a fost găsit.")
    path = (MEDIA_DIR / media_path).resolve()
    if not path.is_relative_to(MEDIA_DIR.resolve()):
        raise HTTPException(404,"Fișierul nu a fost găsit.")
    filename = path.stem
    lesson_id = re.sub(r"_(ro|en)$","",filename) if media_path.startswith("audio/") else filename
    url = "/media/"+media_path
    with closing(get_db_connection()) as conn:
        row = conn.execute("""SELECT course_id FROM lessons WHERE id=? OR audio_url=? OR audio_url_ro=?
            OR audio_url_en=? OR video_url=? LIMIT 1""",(lesson_id,url,url,url,url)).fetchone()
        if not row:
            raise HTTPException(404,"Fișierul nu a fost găsit.")
        check_course_access(conn,row["course_id"],user)
    if not path.is_file():
        raise HTTPException(404,"Fișierul nu a fost generat încă.")
    return FileResponse(path,headers={"Cache-Control":"private, no-store"})


for router in (auth.router,community.router,books.router,courses.router,lessons.router,flashcards.router,
    quizzes.router,demo.router,export.router,groups.router,study.router):
    app.include_router(router)


@app.get("/")
def root():
    return {"app":"4Next","tagline":"Înțelegi. Exersezi. Îți rămâne.","status":"ready","docs":"/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app",host="0.0.0.0",port=8000,reload=True)
