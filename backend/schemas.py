from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="The user's full name")
    email: EmailStr = Field(..., description="A valid email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class IncidentSubmission(BaseModel):
    description: str = Field(..., min_length=10, max_length=500, description="Detailed description of the issue")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    image_name: str = Field(..., description="Uploaded image file name")
    module: str = Field("road", description="The CivicGuard module (road, water, environment, cleancity, asset)")

class RewardRedeem(BaseModel):
    reward_id: str = Field(..., description="The ID of the reward to redeem")

class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="The new status (e.g. reported, dispatched, resolved)")
    work_order_id: Optional[str] = Field(None, description="Optional associated work order ID")
