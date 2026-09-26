from fastapi_users import schemas as fastapi_schemas

# Schema returned to clients (e.g., in responses)
class UserRead(fastapi_schemas.BaseUser[int]):
    pass

# Schema used when creating a new user (e.g., in POST /register)
class UserCreate(fastapi_schemas.BaseUserCreate):
    pass

# Schema used when updating a user
class UserUpdate(fastapi_schemas.BaseUserUpdate):
    pass
