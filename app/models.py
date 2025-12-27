from pydantic import BaseModel, EmailStr


class ProcessingRequest(BaseModel):
    email: EmailStr
    model: str = "u2net"
    output_format: str = "png"
    quality: int = 95
    scale: float = 1.0


class ProcessingStatus(BaseModel):
    status: str
    email: EmailStr
    filename: str | None = None
    error: str | None = None
