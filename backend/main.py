from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
import os
import contextlib
from dotenv import load_dotenv

# Ensure .env is loaded from the correct path
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from app.routes import auth, profile, workout, community, chat, admin, store, public, support, support_ws
from app.database import init_db

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Database...", flush=True)
    try:
        await init_db()
        print("System Ready.", flush=True)
    except Exception as e:
        print(f"DATABASE FATAL ERROR: {str(e)}", flush=True)
    yield

app = FastAPI(lifespan=lifespan)

import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from collections import defaultdict

# High-performance rate limiting memory stores
IP_REQUEST_LOGS = defaultdict(list)
AUTH_ATTEMPT_LOGS = defaultdict(list)

# Redis setup (with safe fallback)
REDIS_URL = os.getenv("REDIS_URL")
redis_client = None
if REDIS_URL:
    try:
        import redis # type: ignore
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        redis_client.ping()
        print("Connected to Redis for rate limiting.", flush=True)
    except Exception as e:
        print(f"[WARNING] Redis connection failed, falling back to memory: {e}", flush=True)
        redis_client = None

@app.middleware("http")
async def rate_limiting_shield(request: Request, call_next):
    path = request.url.path
    if path.startswith("/uploads") or path == "/" or path == "/health" or path.startswith("/api/community/ws") or path.startswith("/api/support-ws"):
        return await call_next(request)
        
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # 1. Brute-Force Login & Register Shield (Max 10 calls per 60s)
    if "/api/auth/login" in path or "/api/auth/register" in path:
        if redis_client:
            auth_key = f"auth_rate:{client_ip}"
            current_auths = redis_client.incr(auth_key)
            if current_auths == 1:
                redis_client.expire(auth_key, 60)
            if current_auths > 10:
                return JSONResponse(status_code=429, content={"detail": "Too many authentication attempts. Please wait 60 seconds."})
        else:
            auth_timestamps = AUTH_ATTEMPT_LOGS[client_ip]
            auth_timestamps = [t for t in auth_timestamps if now - t < 60]
            AUTH_ATTEMPT_LOGS[client_ip] = auth_timestamps
            if len(auth_timestamps) >= 10:
                return JSONResponse(status_code=429, content={"detail": "Too many authentication attempts. Please wait 60 seconds."})
            AUTH_ATTEMPT_LOGS[client_ip].append(now)
        
    # 2. General Flood Shield (Max 120 calls per 10s)
    if redis_client:
        ip_key = f"ip_rate:{client_ip}"
        current_reqs = redis_client.incr(ip_key)
        if current_reqs == 1:
            redis_client.expire(ip_key, 10)
        if current_reqs > 120:
            return JSONResponse(status_code=429, content={"detail": "Network activity too high. Slow down to guarantee system stability."})
    else:
        ip_timestamps = IP_REQUEST_LOGS[client_ip]
        ip_timestamps = [t for t in ip_timestamps if now - t < 10]
        IP_REQUEST_LOGS[client_ip] = ip_timestamps
        
        if len(ip_timestamps) >= 120:
            return JSONResponse(status_code=429, content={"detail": "Network activity too high. Slow down to guarantee system stability."})
        IP_REQUEST_LOGS[client_ip].append(now)
        
        # Self-cleaning memory guard to prevent leaks
        if len(IP_REQUEST_LOGS) > 5000:
            cleaned_ips = [ip for ip, times in list(IP_REQUEST_LOGS.items()) if not times or now - times[-1] > 60]
            for ip in cleaned_ips:
                if ip in IP_REQUEST_LOGS:
                    del IP_REQUEST_LOGS[ip]
                    
    return await call_next(request)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# PRO-FIX: Strict Origin CORS for production stability
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:10000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:10000",
        "https://gotrip.vercel.app"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routes
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(workout.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(store.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(support.router, prefix="/api")
app.include_router(support_ws.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "Travel Backend Online", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

import uvicorn
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"Starting server on port {port}...", flush=True)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)