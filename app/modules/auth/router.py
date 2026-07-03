

from fastapi import APIRouter, Body


auth_router = APIRouter(
    prefix="/api/v1"
)

@auth_router.get("/health")
async def get_health_info():
    return {
        "message": "Success: Service is running"
    }

@auth_router.post("/login")
async def user_login(data: dict = Body(...)):
    return {
        "message": "User Logged in",
        "data": {
            "access": "alsdfkja lasjdfldasjkflasjflj"
        }
    }