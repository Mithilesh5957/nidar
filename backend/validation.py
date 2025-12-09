# validation.py
"""Pydantic validation models for NIDAR API"""
from pydantic import BaseModel, Field, validator, constr
from typing import Optional, List
from enum import Enum

# ==================== Enums ====================
class VehicleStatus(str, Enum):
    connected = "connected"
    disconnected = "disconnected"
    error = "error"

class MissionStatus(str, Enum):
    uploaded = "uploaded"
    active = "active"
    completed = "completed"
    aborted = "aborted"

# ==================== Detection Models ====================
class DetectionMetadata(BaseModel):
    """Metadata for detection upload"""
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    conf: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection confidence score")
    
    @validator('lat', 'lon')
    def validate_coordinates(cls, v, field):
        if v is not None:
            if field.name == 'lat' and abs(v) < 0.0001:
                raise ValueError("Latitude too close to zero, likely invalid")
            if field.name == 'lon' and abs(v) < 0.0001:
                raise ValueError("Longitude too close to zero, likely invalid")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "lat": 28.5355,
                "lon": 77.3910,
                "conf": 0.95
            }
        }

class DetectionCreate(BaseModel):
    """Detection creation request"""
    vehicle_id: constr(min_length=1, max_length=50)
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    lon: Optional[float] = Field(None, ge=-180.0, le=180.0)
    conf: Optional[float] = Field(None, ge=0.0, le=1.0)
    img_path: str

class DetectionResponse(BaseModel):
    """Detection response model"""
    id: int
    vehicle_id: str
    lat: Optional[float]
    lon: Optional[float]
    conf: Optional[float]
    img: str
    ts: int
    approved: bool
    delivered: bool = False
    
    class Config:
        from_attributes = True

# ==================== Mission Models ====================
class MissionWaypoint(BaseModel):
    """Single mission waypoint"""
    seq: int = Field(ge=0, description="Waypoint sequence number")
    frame: int = Field(ge=0, le=3, description="MAVLink frame type")
    command: int = Field(ge=0, le=65535, description="MAVLink command ID")
    param1: float = Field(0.0, description="Parameter 1")
    param2: float = Field(0.0, description="Parameter 2")
    x: float = Field(description="Latitude or X position")
    y: float = Field(description="Longitude or Y position")
    z: float = Field(description="Altitude or Z position")
    
    @validator('z')
    def validate_altitude(cls, v):
        if v < 0 or v > 1000:
            raise ValueError("Altitude must be between 0-1000m")
        return v

class MissionUploadRequest(BaseModel):
    """Mission upload request"""
    vehicle_id: constr(min_length=1, max_length=50)
    waypoints: List[MissionWaypoint] = Field(min_items=1, max_items=100)
    
    class Config:
        schema_extra = {
            "example": {
                "vehicle_id": "delivery",
                "waypoints": [
                    {
                        "seq": 0,
                        "frame": 0,
                        "command": 22,
                        "param1": 0,
                        "param2": 0,
                        "x": 28.5355,
                        "y": 77.3910,
                        "z": 60.0
                    }
                ]
            }
        }

class ApproveDetectionRequest(BaseModel):
    """Detection approval request"""
    delivery_vehicle_id: constr(min_length=1, max_length=50) = Field(
        default="delivery",
        description="Vehicle ID of delivery drone"
    )
    
    @validator('delivery_vehicle_id')
    def validate_vehicle_id(cls, v):
        allowed = ['delivery', 'delivery1', 'delivery2']  # Configure as needed
        if v not in allowed:
            raise ValueError(f"Invalid delivery vehicle. Allowed: {allowed}")
        return v

# ==================== Vehicle Models ====================
class VehicleResponse(BaseModel):
    """Vehicle details response"""
    vehicle_id: str
    name: str
    sysid: Optional[int]
    last_seen: Optional[int]
    last_pos_lat: Optional[float]
    last_pos_lon: Optional[float]
    last_pos_alt: Optional[float]
    battery: Optional[int] = Field(None, ge=0, le=100)
    status: VehicleStatus
    
    class Config:
        from_attributes = True

# ==================== File Upload Validation ====================
class FileUploadValidator:
    """Validate file uploads"""
    
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/webp'
    }
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    @staticmethod
    async def validate_image(file, max_size: int = MAX_FILE_SIZE) -> None:
        """Validate uploaded image file"""
        # Check content type
        if file.content_type not in FileUploadValidator.ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Invalid file type: {file.content_type}. "
                f"Allowed: {', '.join(FileUploadValidator.ALLOWED_IMAGE_TYPES)}"
            )
        
        # Check file extension
        import os
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in FileUploadValidator.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension: {ext}. "
                f"Allowed: {', '.join(FileUploadValidator.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if size > max_size:
            raise ValueError(
                f"File too large: {size / 1024 / 1024:.2f}MB. "
                f"Max: {max_size / 1024 / 1024:.0f}MB"
            )
        
        if size == 0:
            raise ValueError("Empty file not allowed")

# ==================== Query Parameter Models ====================
class TelemetryQueryParams(BaseModel):
    """Query parameters for telemetry endpoint"""
    limit: int = Field(500, ge=1, le=5000, description="Number of points to return")
    
class PaginationParams(BaseModel):
    """Generic pagination parameters"""
    offset: int = Field(0, ge=0, description="Offset for pagination")
    limit: int = Field(50, ge=1, le=200, description="Items per page")

# ==================== Error Response Models ====================
class ErrorDetail(BaseModel):
    """Error detail model"""
    field: Optional[str] = None
    message: str
    type: str

class ErrorResponse(BaseModel):
    """Standardized error response"""
    detail: str
    errors: Optional[List[ErrorDetail]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Validation error",
                "errors": [
                    {
                        "field": "lat",
                        "message": "ensure this value is greater than or equal to -90.0",
                        "type": "value_error.number.not_ge"
                    }
                ]
            }
        }
