"""
Operations Endpoints: History Audit Log, Analyst Feedback, and Triage Workflow Status
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List

from rescueai.api.schemas import (
    StatusUpdateRequest, FeedbackRequest, FeedbackResponse
)
from rescueai.database import (
    set_triage_status, add_feedback_entry, get_feedback_summary,
    get_history_entries, clear_history_entries
)

router = APIRouter(tags=["Operations & Triage"])


@router.put("/status/{tweet_id}")
def update_tweet_status(tweet_id: str, body: StatusUpdateRequest):
    """
    Updates the operational triage status of a message ('reviewed', 'flagged', 'not relevant', 'unreviewed').
    Persisted directly in SQLite.
    """
    try:
        return set_triage_status(tweet_id=tweet_id, status=body.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(body: FeedbackRequest):
    """
    Records analyst feedback on prediction accuracy (correct / incorrect + suggested class).
    Persisted to SQLite without altering frozen weights.
    """
    fb_id = add_feedback_entry(
        tweet_id=body.tweet_id,
        raw_text=body.raw_text,
        predicted_label=body.predicted_label,
        is_correct=body.is_correct,
        user_label=body.user_label,
        notes=body.notes
    )
    return FeedbackResponse(status="saved", id=fb_id)


@router.get("/feedback/stats")
def get_feedback_stats():
    """Returns analyst agreement rate and per-class feedback breakdown."""
    return get_feedback_summary()


@router.get("/history")
def list_history(
    category: Optional[str] = None,
    low_conf_only: Optional[bool] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """Retrieves paginated prediction audit history from SQLite."""
    items, total = get_history_entries(
        category=category,
        low_conf_only=low_conf_only,
        q=q,
        page=page,
        size=size
    )
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }


@router.delete("/history")
def delete_history():
    """Clears all entries in the prediction audit history."""
    deleted = clear_history_entries()
    return {"status": "cleared", "deleted_rows": deleted}
