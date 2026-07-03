from fastapi import APIRouter, FastAPI
from core.database import engine
from sqlalchemy import text
from app.modules.auth.router import auth_router


app = FastAPI(
    title="Student Service"
)

@app.on_event("startup")
def startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("✅ MySQL Connected")

app.include_router(auth_router)