"""
Model Benchmarks, Interactive Confusion Matrix, and Review Threshold Analysis Endpoints
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import List

from rescueai.api.schemas import (
    ModelBenchmarkItem, ConfusionMatrixResponse, ConfusionCellResponse,
    ThresholdAnalysisResponse
)

router = APIRouter(prefix="/models", tags=["Model Analytics"])


@router.get("", response_model=List[ModelBenchmarkItem])
def list_models(request: Request):
    """Returns comparative performance metrics for all four trained ML algorithms."""
    models_svc = request.app.state.models_service
    items = []
    for b in models_svc.benchmarks:
        is_sel = "[CHAMPION]" in b["Model"]
        items.append(ModelBenchmarkItem(
            model=b["Model"],
            type=b["Type"],
            train_time_s=float(b.get("Train Time (s)", 0.0)),
            test_accuracy=float(b.get("Test Accuracy", 0.0)),
            macro_precision=float(b.get("Macro Precision", 0.0)),
            macro_recall=float(b.get("Macro Recall", 0.0)),
            macro_f1=float(b.get("Macro F1", 0.0)),
            weighted_f1=float(b.get("Weighted F1", 0.0)),
            cat_0_recall=float(b.get("Cat 0 Recall", 0.0)),
            cat_0_f1=float(b.get("Cat 0 F1", 0.0)),
            strengths=b.get("Strengths", ""),
            weaknesses=b.get("Weaknesses", ""),
            is_selected=is_sel
        ))
    return items


@router.get("/{name}/confusion", response_model=ConfusionMatrixResponse)
def get_confusion(
    request: Request,
    name: str,
    normalize: bool = Query(False)
):
    """Computes dynamic 5x5 confusion matrix on real test data."""
    models_svc = request.app.state.models_service
    data_svc = request.app.state.data_service
    
    if name not in ("champion", "logistic_regression", "linear_svm", "naive_bayes", "random_forest"):
        raise HTTPException(status_code=400, detail=f"Unknown model name '{name}'")
        
    res = models_svc.get_confusion_matrix_data(name, normalize=normalize, test_df=data_svc.df_test)
    return res


@router.get("/{name}/confusion/cell", response_model=ConfusionCellResponse)
def get_confusion_cell(
    request: Request,
    name: str,
    true_cls: int = Query(..., alias="true", ge=0, le=4),
    pred_cls: int = Query(..., alias="pred", ge=0, le=4),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Retrieves real test set messages that fall inside a specific cell of the confusion matrix."""
    models_svc = request.app.state.models_service
    data_svc = request.app.state.data_service
    
    if name not in ("champion", "logistic_regression", "linear_svm", "naive_bayes", "random_forest"):
        raise HTTPException(status_code=400, detail=f"Unknown model name '{name}'")
        
    return models_svc.get_confusion_cell_samples(
        model_name=name,
        true_label=true_cls,
        pred_label=pred_cls,
        test_df=data_svc.df_test,
        page=page,
        size=size
    )


@router.get("/{name}/threshold", response_model=ThresholdAnalysisResponse)
def get_threshold(
    request: Request,
    name: str,
    t: float = Query(0.0, ge=0.0, le=1.0)
):
    """
    Simulates sending messages with confidence < t to manual analyst review.
    Returns retained message accuracy, macro F1, and per-class recall.
    """
    models_svc = request.app.state.models_service
    data_svc = request.app.state.data_service
    
    if name not in ("champion", "logistic_regression", "linear_svm", "naive_bayes", "random_forest"):
        raise HTTPException(status_code=400, detail=f"Unknown model name '{name}'")
        
    return models_svc.get_threshold_analysis(name, t, data_svc.df_test)
