from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    nickname: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserInDB(BaseModel):
    id: int
    email: str
    nickname: str
    
    class Config:
        orm_mode = True