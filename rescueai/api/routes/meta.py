"""
Metadata and System Health Endpoints
"""

from fastapi import APIRouter, Request
from typing import List

from rescueai.constants import CATEGORY_CONFIG
from rescueai.api.schemas import HealthResponse, MetaResponse, CategoryInfo, EventSummary

router = APIRouter(tags=["Metadata"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@router.get("/meta", response_model=MetaResponse)
def get_meta(request: Request):
    """Returns champion model info, categories, and dataset summary statistics."""
    data_svc = request.app.state.data_service
    models_svc = request.app.state.models_service
    
    categories = [
        CategoryInfo(
            id=cat_id,
            name=cfg["name"],
            color=cfg["color"],
            urgency=cfg["urgency"],
            description=cfg["description"]
        )
        for cat_id, cfg in CATEGORY_CONFIG.items()
    ]
    
    total = len(data_svc.df_train) + len(data_svc.df_dev) + len(data_svc.df_test)
    
    return MetaResponse(
        model_name="Logistic Regression (Balanced)",
        test_macro_f1=0.4746,
        test_accuracy=0.5060,
        dataset_name="CrisisMMD v2.0",
        total_samples=total,
        train_samples=len(data_svc.df_train),
        dev_samples=len(data_svc.df_dev),
        test_samples=len(data_svc.df_test),
        disaster_events_count=len(request.app.state.data_service.get_events_summary()),
        categories=categories
    )


@router.get("/events", response_model=List[EventSummary])
def get_events(request: Request):
    """Returns disaster event clusters with real coordinates, types, dates, and message counts."""
    data_svc = request.app.state.data_service
    return data_svc.get_events_summary()
