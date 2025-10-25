"""
Endpoints for managing announcements
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from datetime import datetime
from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Dummy implementation: replace with real token validation
    user = teachers_collection.find_one({"_id": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
def list_announcements():
    """List all announcements (active and expired)"""
    docs = announcements_collection.find({}, {"_id": 1, "message": 1, "start_date": 1, "expiration_date": 1})
    result = []
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        result.append(doc)
    return result

@router.post("/add", response_model=dict)
def add_announcement(message: str, expiration_date: str, start_date: Optional[str] = None, user=Depends(get_current_user)):
    """Add a new announcement (signed-in users only)"""
    if not expiration_date:
        raise HTTPException(status_code=400, detail="Expiration date required")
    announcement = {
        "message": message,
        "expiration_date": expiration_date,
        "start_date": start_date
    }
    result = announcements_collection.insert_one(announcement)
    return {"_id": str(result.inserted_id), **announcement}

@router.put("/{announcement_id}", response_model=dict)
def update_announcement(announcement_id: str, message: Optional[str] = None, expiration_date: Optional[str] = None, start_date: Optional[str] = None, user=Depends(get_current_user)):
    """Update an announcement (signed-in users only)"""
    update_fields = {}
    if message is not None:
        update_fields["message"] = message
    if expiration_date is not None:
        update_fields["expiration_date"] = expiration_date
    if start_date is not None:
        update_fields["start_date"] = start_date
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    doc = announcements_collection.find_one({"_id": announcement_id})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.delete("/{announcement_id}", response_model=dict)
def delete_announcement(announcement_id: str, user=Depends(get_current_user)):
    """Delete an announcement (signed-in users only)"""
    result = announcements_collection.find_one_and_delete({"_id": announcement_id})
    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found")
    if result:
        result["_id"] = str(result["_id"])
    return result
