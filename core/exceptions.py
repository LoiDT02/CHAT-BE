from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from constant import AppStatus


def make_error_response(app_status=AppStatus.ERROR_500_INTERNAL_SERVER_ERROR, detail=None):
    if detail is None:
        detail = {}

    return JSONResponse(
        status_code=app_status.status_code,
        content=jsonable_encoder({"detail": detail}),
    )


def make_response_object(data, meta={}):
    return {
        "data": data,
        "meta": meta
    }


async def validation_exception_handler(request: Request, validation_error: RequestValidationError):
    detail = validation_error.errors()[0]
    err_loc = detail.get('loc')
    err_field = err_loc[len(err_loc) - 1]
    err_msg = f"{detail.get('msg')}: {err_field}"
    return make_error_response(app_status=AppStatus.ERROR_400_BAD_REQUEST, detail={
            "name": AppStatus.ERROR_400_BAD_REQUEST.name,
            "message": err_msg
        })


def error_exception_handler(app_status: AppStatus, **kwargs):
    return HTTPException(
        status_code=app_status.status_code,
        detail={
            "name": app_status.name,
            "message": app_status.message.format(**kwargs),
        }
    )
