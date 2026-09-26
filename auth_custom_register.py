from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi_users import schemas
from auth import get_user_db
from password import get_password_hash

router = APIRouter()


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def custom_register(user: schemas.BaseUserCreate, user_db=Depends(get_user_db)):
    existing = await user_db.get_by_email(user.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Accept only fields that a normal public registration is allowed to control.
    # FastAPI Users deliberately excludes privileged account flags here.
    user_dict = user.create_update_dict()

    user_dict["hashed_password"] = get_password_hash(user.password)
    user_dict.pop("password", None)

    # Privileged account state is controlled by the server, never by the request.
    user_dict["is_active"] = True
    user_dict["is_superuser"] = False
    user_dict["is_verified"] = True

    created_user = await user_db.create(user_dict)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"email": created_user.email},
    )
