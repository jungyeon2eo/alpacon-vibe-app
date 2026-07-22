import os
import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from redis import Redis
from rq import Queue

from db import get_conn, init_db

SPROUT_EVERY = 8  # every N grass eaten, a plant sprouts (via the worker)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # seed the fast Redis counter from the persisted total
    with get_conn() as conn:
        row = conn.execute("SELECT grass_eaten FROM game WHERE id = 1").fetchone()
    redis_conn.set("grass:count", int(row[0]) if row else 0)
    yield


app = FastAPI(title="Alpaca Meadow", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

redis_conn = Redis.from_url(os.environ["REDIS_URL"])
queue = Queue("default", connection=redis_conn)


def _state():
    with get_conn() as conn:
        g = conn.execute("SELECT grass_eaten, distance_m FROM game WHERE id = 1").fetchone()
        rows = conn.execute(
            "SELECT species, emoji FROM plants ORDER BY id DESC LIMIT 200"
        ).fetchall()
    plants = [{"species": r[0], "emoji": r[1]} for r in rows]
    return {"grass_eaten": int(g[0]), "distance_m": int(g[1]), "plants": plants}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/state")
def state():
    return _state()


@app.post("/eat")
def eat():
    """The alpaca munches a tuft of grass."""
    count = redis_conn.incr("grass:count")  # fast live counter
    step = random.randint(1, 2)
    with get_conn() as conn:
        conn.execute(
            "UPDATE game SET grass_eaten = %s, distance_m = distance_m + %s WHERE id = 1",
            (int(count), step),
        )
    sprouting = count % SPROUT_EVERY == 0
    if sprouting:
        queue.enqueue("tasks.sprout_plant")
    return {"grass_eaten": int(count), "sprouting": sprouting}


@app.post("/walk")
def walk():
    """Idle progress — the alpaca keeps ambling across the meadow."""
    step = random.randint(2, 5)
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE game SET distance_m = distance_m + %s WHERE id = 1 RETURNING distance_m",
            (step,),
        ).fetchone()
    return {"distance_m": int(row[0])}
