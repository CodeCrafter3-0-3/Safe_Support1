from typing import Optional

from pydantic import BaseModel


class PostInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[object] = None
    duration_of_abuse: Optional[str] = None
    frequency_of_incidents: Optional[str] = None
    preferred_contact_method: Optional[list[str]] = None
    current_situation: Optional[str] = None
    culprit_description: Optional[str] = None
    custom_text: Optional[str] = None


# Pydantic model to validate input
class FileContent(BaseModel):
    filename: str
    content: str
