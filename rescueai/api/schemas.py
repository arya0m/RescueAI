"""
RescueAI Pydantic Schemas for API Requests and Responses.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


class CategoryInfo(BaseModel):
    id: int
    name: str
    color: str
    urgency: str
    description: str


class MetaResponse(BaseModel):
    model_name: str
    test_macro_f1: float
    test_accuracy: float
    dataset_name: str
    total_samples: int
    train_samples: int
    dev_samples: int
    test_samples: int
    disaster_events_count: int
    categories: List[CategoryInfo]


class EventSummary(BaseModel):
    event_id: str
    display_name: str
    disaster_type: str
    lat: float
    lon: float
    source: str
    total_messages: int
    start_date: str
    end_date: str
    counts_by_class: Dict[str, int]
    urgency_counts: Dict[str, int]
    high_urgency_percent: float


class MessageItem(BaseModel):
    tweet_id: str
    event_name: str
    tweet_text: str
    clean_text: str
    timestamp: str
    true_label: int
    true_category: str
    predicted_label: int
    predicted_category: str
    confidence: float
    urgency: str
    is_correct: bool
    status: str
    probabilities: Dict[str, float]


class PaginatedMessagesResponse(BaseModel):
    total: int
    page: int
    size: int
    total_pages: int
    items: List[MessageItem]


class TermAttribution(BaseModel):
    term: str
    score: float
    runner_score: float
    favored: str
    category: str


class MessageDetail(MessageItem):
    terms: List[TermAttribution]


class TimelineBucket(BaseModel):
    time: str
    total: int
    counts: Dict[str, int]


class ReplayMessageItem(BaseModel):
    tweet_id: str
    timestamp: str
    event_name: str
    tweet_text: str
    clean_text: str
    true_label: int
    true_category: str
    predicted_label: int
    predicted_category: str
    confidence: float
    probabilities: Dict[str, float]
    urgency: str


class PredictRequest(BaseModel):
    text: str = Field(..., max_length=1000, description="Raw disaster tweet text to classify")


class RunnerUpInfo(BaseModel):
    label: int
    category: str
    confidence: float
    gap: float


class PredictResponse(BaseModel):
    raw_text: str
    clean_text: str
    predicted_label: int
    predicted_category: str
    urgency: str
    confidence: float
    probabilities: Dict[str, float]
    is_low_confidence: bool
    runner_up: Optional[RunnerUpInfo] = None
    terms: List[TermAttribution]


class PredictBatchItem(BaseModel):
    index: int
    text: str
    predicted_label: int
    predicted_category: str
    confidence: float
    urgency: str


class PredictBatchResponse(BaseModel):
    total_rows: int
    mean_confidence: float
    category_summary: Dict[str, int]
    predictions: List[PredictBatchItem]


class AblateRequest(BaseModel):
    text: str = Field(..., max_length=1000)
    remove: List[str] = Field(..., min_length=1)


class AblateResponse(BaseModel):
    original: PredictResponse
    ablated: PredictResponse
    removed_tokens: List[str]
    prediction_changed: bool
    confidence_delta: float


class ModelBenchmarkItem(BaseModel):
    model: str
    type: str
    train_time_s: float
    test_accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    cat_0_recall: float
    cat_0_f1: float
    strengths: str
    weaknesses: str
    is_selected: bool = False


class ConfusionMatrixResponse(BaseModel):
    model_name: str
    normalized: bool
    labels: List[str]
    matrix: List[List[float]]


class ConfusionCellResponse(BaseModel):
    true_label: int
    true_category: str
    predicted_label: int
    predicted_category: str
    total_count: int
    page: int
    size: int
    items: List[Dict[str, Any]]


class ThresholdAnalysisResponse(BaseModel):
    model_name: str
    threshold: float
    total_messages: int
    flagged_count: int
    flagged_percent: float
    retained_count: int
    retained_accuracy: float
    retained_macro_f1: float
    per_class_recall: Dict[str, float]


class TermWeight(BaseModel):
    term: str
    weight: float


class ClassTermsResponse(BaseModel):
    class_index: int
    category_name: str
    color: str
    terms: List[TermWeight]


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Must be 'unreviewed', 'reviewed', 'flagged', or 'irrelevant'")


class FeedbackRequest(BaseModel):
    raw_text: str
    predicted_label: int
    is_correct: bool
    tweet_id: Optional[str] = None
    user_label: Optional[int] = None
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str = "saved"
    id: int
