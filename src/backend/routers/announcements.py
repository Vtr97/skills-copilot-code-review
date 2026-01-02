"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("/active")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (within date range)"""
    try:
        current_time = datetime.utcnow().isoformat()
        
        # Find announcements that are currently active
        announcements = list(announcements_collection.find({
            "$and": [
                {"end_date": {"$gte": current_time}},
                {
                    "$or": [
                        {"start_date": None},
                        {"start_date": {"$lte": current_time}}
                    ]
                }
            ]
        }))
        
        # Convert ObjectId to string for JSON serialization
        for announcement in announcements:
            announcement["_id"] = str(announcement["_id"])
        
        return announcements
    except Exception as e:
        print(f"Error fetching active announcements: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch announcements")


@router.get("")
def get_all_announcements() -> List[Dict[str, Any]]:
    """Get all announcements (for management interface)"""
    try:
        announcements = list(announcements_collection.find().sort("created_at", -1))
        
        # Convert ObjectId to string for JSON serialization
        for announcement in announcements:
            announcement["_id"] = str(announcement["_id"])
        
        return announcements
    except Exception as e:
        print(f"Error fetching all announcements: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch announcements")


@router.post("")
def create_announcement(
    message: str,
    end_date: str,
    username: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement (requires authentication)"""
    try:
        # Verify user exists and is authenticated
        teacher = teachers_collection.find_one({"_id": username})
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Validate dates
        try:
            datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if start_date:
                datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
        
        # Create announcement
        announcement = {
            "message": message,
            "start_date": start_date,
            "end_date": end_date,
            "created_by": username,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = announcements_collection.insert_one(announcement)
        announcement["_id"] = str(result.inserted_id)
        
        return announcement
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating announcement: {e}")
        raise HTTPException(status_code=500, detail="Failed to create announcement")


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    message: str,
    end_date: str,
    username: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing announcement (requires authentication)"""
    try:
        # Verify user exists and is authenticated
        teacher = teachers_collection.find_one({"_id": username})
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Validate announcement ID
        try:
            obj_id = ObjectId(announcement_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid announcement ID")
        
        # Validate dates
        try:
            datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if start_date:
                datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
        
        # Update announcement
        update_data = {
            "message": message,
            "start_date": start_date,
            "end_date": end_date
        }
        
        result = announcements_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        # Return updated announcement
        announcement = announcements_collection.find_one({"_id": obj_id})
        announcement["_id"] = str(announcement["_id"])
        
        return announcement
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating announcement: {e}")
        raise HTTPException(status_code=500, detail="Failed to update announcement")


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    username: str
) -> Dict[str, str]:
    """Delete an announcement (requires authentication)"""
    try:
        # Verify user exists and is authenticated
        teacher = teachers_collection.find_one({"_id": username})
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Validate announcement ID
        try:
            obj_id = ObjectId(announcement_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid announcement ID")
        
        # Delete announcement
        result = announcements_collection.delete_one({"_id": obj_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        return {"message": "Announcement deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting announcement: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete announcement")
