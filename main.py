from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from core.database import engine
from app.modules.auth.router import auth_router
from app.grpc.server import start_grpc_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database check
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("✅ MySQL Connected")

    # Start gRPC server
    grpc_server = await start_grpc_server()

    yield

    # Shutdown gRPC server
    await grpc_server.stop(grace=5)
    print("✅ gRPC Server stopped")


app = FastAPI(
    title="Student Service",
    lifespan=lifespan,
)

app.include_router(auth_router)