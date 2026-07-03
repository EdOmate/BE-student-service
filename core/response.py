from fastapi.responses import JSONResponse


class SuccessResponse(JSONResponse):
    def __init__(
        self,
        result: bool = True,
        data=None,
        message: str = "Success",
        status_code: int = 200,
    ):
        content = {
            "result": result,
            "message": message,
            "data": data,
        }
        super().__init__(content=content, status_code=status_code)


class ErrorResponse(JSONResponse):
    def __init__(
        self,
        result: bool = False,
        data=None,
        message: str = "Error",
        status_code: int = 400,
        errors=None,
    ):
        content = {
            "result": result,
            "message": message,
            "data": data,
            "errors": errors or [],
        }
        super().__init__(content=content, status_code=status_code)