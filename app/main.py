import hashlib
import hmac
import os
import random
import re
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from redis import Redis
from rq import Queue

from db import get_conn, init_db

SECRET = os.environ.get("APP_SECRET", "alpaca-meadow-dev-secret").encode()
SPROUT_EVERY = 8
ID_RE = re.compile(r"^[a-z0-9_]{2,20}$")
PIN_RE = re.compile(r"^[0-9]{4,6}$")


def hash_pin(pin: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt_hex), 120_000).hex()


def make_token(player_id: str) -> str:
    sig = hmac.new(SECRET, player_id.encode(), hashlib.sha256).hexdigest()
    return f"{player_id}.{sig}"


def verify_token(token: str):
    if not token or "." not in token:
        return None
    player_id, sig = token.rsplit(".", 1)
    good = hmac.new(SECRET, player_id.encode(), hashlib.sha256).hexdigest()
    return player_id if hmac.compare_digest(sig, good) else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Alpaca Meadow", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

redis_conn = Redis.from_url(os.environ["REDIS_URL"])
queue = Queue("default", connection=redis_conn)


def require_player(x_player_token: str = Header(default="")) -> str:
    player_id = verify_token(x_player_token)
    if not player_id:
        raise HTTPException(status_code=401, detail="login required")
    return player_id


class Login(BaseModel):
    player_id: str
    pin: str


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/login")
def login(body: Login):
    """Create a profile on first use, or resume an existing one with the right PIN."""
    pid = body.player_id.strip().lower()
    pin = body.pin.strip()
    if not ID_RE.match(pid):
        raise HTTPException(status_code=400, detail="ID: 2–20 chars (a–z, 0–9, _)")
    if not PIN_RE.match(pin):
        raise HTTPException(status_code=400, detail="PIN: 4–6 digits")
    with get_conn() as conn:
        row = conn.execute("SELECT pin_hash, salt FROM players WHERE id = %s", (pid,)).fetchone()
        if row:
            if not hmac.compare_digest(hash_pin(pin, row[1]), row[0]):
                raise HTTPException(status_code=401, detail="wrong PIN for that ID")
            returning = True
        else:
            salt = os.urandom(16).hex()
            conn.execute(
                "INSERT INTO players (id, pin_hash, salt) VALUES (%s, %s, %s)",
                (pid, hash_pin(pin, salt), salt),
            )
            returning = False
    return {"token": make_token(pid), "player_id": pid, "returning": returning}


def _state(pid: str):
    with get_conn() as conn:
        g = conn.execute(
            "SELECT grass_eaten, distance_m FROM players WHERE id = %s", (pid,)
        ).fetchone()
        rows = conn.execute(
            "SELECT species, emoji FROM plants WHERE player_id = %s ORDER BY id DESC LIMIT 300",
            (pid,),
        ).fetchall()
    plants = [{"species": r[0], "emoji": r[1]} for r in rows]
    return {"player_id": pid, "grass_eaten": int(g[0]), "distance_m": int(g[1]), "plants": plants}


@app.get("/state")
def state(pid: str = Depends(require_player)):
    return _state(pid)


@app.post("/eat")
def eat(pid: str = Depends(require_player)):
    """The alpaca munches a tuft of grass."""
    step = random.randint(1, 2)
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE players SET grass_eaten = grass_eaten + 1, distance_m = distance_m + %s, "
            "updated_at = now() WHERE id = %s RETURNING grass_eaten",
            (step, pid),
        ).fetchone()
    count = int(row[0])
    redis_conn.incr(f"grass:{pid}")  # live counter (best-effort)
    sprouting = count % SPROUT_EVERY == 0
    if sprouting:
        queue.enqueue("tasks.sprout_plant", pid)
    return {"grass_eaten": count, "sprouting": sprouting}


@app.post("/walk")
def walk(pid: str = Depends(require_player)):
    """Idle progress — the alpaca keeps ambling across the meadow."""
    step = random.randint(2, 5)
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE players SET distance_m = distance_m + %s, updated_at = now() "
            "WHERE id = %s RETURNING distance_m",
            (step, pid),
        ).fetchone()
    return {"distance_m": int(row[0])}
