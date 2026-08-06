from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from core.database import engine
from app.modules.academics.router import academics_router
from app.modules.auth.router import auth_router
from app.modules.dashboard.router import dashboard_router
from app.modules.students.router import student_router
from app.modules.lms.router import lms_router
from app.modules.utils.router import utils_router
from app.grpc.server import start_grpc_server


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


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


@app.get("/", include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"service_name": app.title},
    )


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(academics_router)
app.include_router(student_router)
app.include_router(lms_router)
app.include_router(utils_router)
