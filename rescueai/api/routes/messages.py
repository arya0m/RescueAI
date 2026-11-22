"""
Disaster Relief Messages, Timeline, and Replay Endpoints
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional, List
import math

from rescueai.api.schemas import (
    PaginatedMessagesResponse, MessageDetail, TimelineBucket, ReplayMessageItem
)

router = APIRouter(tags=["Messages"])


@router.get("/messages", response_model=PaginatedMessagesResponse)
def list_messages(
    request: Request,
    split: str = Query("test", pattern="^(test|train|dev)$"),
    event: Optional[str] = None,
    true_cls: Optional[int] = Query(None, ge=0, le=4),
    pred_cls: Optional[int] = Query(None, ge=0, le=4),
    correct: Optional[bool] = None,
    min_conf: Optional[float] = Query(None, ge=0.0, le=1.0),
    q: Optional[str] = None,
    status: Optional[str] = Query(None, pattern="^(reviewed|flagged|irrelevant|unreviewed)$"),
    sort: str = Query("timestamp", pattern="^(timestamp|confidence|tweet_id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200)
):
    """Retrieves paginated and filtered disaster messages with live triage status."""
    data_svc = request.app.state.data_service
    items, total = data_svc.get_messages(
        split=split,
        event=event,
        true_cls=true_cls,
        pred_cls=pred_cls,
        correct=correct,
        min_conf=min_conf,
        q=q,
        status=status,
        sort=sort,
        order=order,
        page=page,
        size=size
    )
    
    total_pages = math.ceil(total / size) if total > 0 else 1
    
    return PaginatedMessagesResponse(
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
        items=items
    )


@router.get("/messages/{tweet_id}", response_model=MessageDetail)
def get_message(request: Request, tweet_id: str):
    """Retrieves single disaster message with feature attribution explanation."""
    data_svc = request.app.state.data_service
    msg = data_svc.get_message_by_id(tweet_id)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Tweet ID '{tweet_id}' not found in dataset")
    return msg


@router.get("/timeline", response_model=List[TimelineBucket])
def get_timeline(
    request: Request,
    event: Optional[str] = None,
    bucket: str = Query("day", pattern="^(day|hour)$")
):
    """Returns time-series frequency counts grouped by predicted category."""
    data_svc = request.app.state.data_service
    return data_svc.get_timeline(event=event, bucket=bucket)


@router.get("/replay", response_model=List[ReplayMessageItem])
def get_replay(
    request: Request,
    event: Optional[str] = None
):
    """
    Returns ordered stream of test set messages in strict chronological order
    for the operations console live replay feature.
    """
    data_svc = request.app.state.data_service
    return data_svc.get_replay_stream(event=event)
