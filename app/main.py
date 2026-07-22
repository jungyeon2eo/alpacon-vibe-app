import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from redis import Redis
from rq import Queue

from db import get_conn, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Alpacon Exercise · URL Health Board", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

redis_conn = Redis.from_url(os.environ["REDIS_URL"])
queue = Queue("default", connection=redis_conn)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/")
def index(request: Request):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, url, status, http_status, latency_ms, checked_at, created_at "
            "FROM checks ORDER BY id DESC LIMIT 50"
        ).fetchall()
    checks = [
        {
            "id": r[0],
            "url": r[1],
            "status": r[2],
            "http_status": r[3],
            "latency_ms": r[4],
            "checked_at": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]
    return templates.TemplateResponse("index.html", {"request": request, "checks": checks})


@app.post("/check")
def create_check(url: str = Form(...)):
    with get_conn() as conn:
        row = conn.execute(
            "INSERT INTO checks (url, status) VALUES (%s, 'queued') RETURNING id", (url,)
        ).fetchone()
        check_id = row[0]
    queue.enqueue("tasks.check_url", check_id, url)
    return RedirectResponse("/", status_code=303)
