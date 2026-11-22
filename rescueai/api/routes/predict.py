"""
Inference Endpoints: Real-Time Prediction, Token Ablation, and CSV Batch Processing
"""

import io
import pandas as pd
from fastapi import APIRouter, Request, HTTPException, UploadFile, File

from rescueai.api.schemas import (
    PredictRequest, PredictResponse, AblateRequest, AblateResponse,
    PredictBatchResponse
)
from rescueai.database import add_history_entry

router = APIRouter(tags=["Inference"])


@router.post("/predict", response_model=PredictResponse)
def predict_message(request: Request, body: PredictRequest):
    """
    Classifies a raw disaster message in real time.
    Returns predicted label, calibrated probability distribution,
    low-confidence warning (if top < 0.50 or gap < 0.10), runner-up class,
    and term attributions.
    """
    models_svc = request.app.state.models_service
    res = models_svc.predict(body.text)
    
    # Save to history database
    add_history_entry(
        raw_text=body.text,
        clean_text=res["clean_text"],
        predicted_label=res["predicted_label"],
        predicted_category=res["predicted_category"],
        confidence=res["confidence"],
        urgency=res["urgency"],
        is_low_confidence=res["is_low_confidence"],
        runner_up_category=res["runner_up"]["category"] if res["runner_up"] else None,
        runner_up_confidence=res["runner_up"]["confidence"] if res["runner_up"] else None
    )
    
    return res


@router.post("/predict/ablate", response_model=AblateResponse)
def ablate_prediction(request: Request, body: AblateRequest):
    """
    Ablates (removes) specific tokens to demonstrate causal Bag-of-Words mechanics.
    Returns comparison between original and ablated predictions.
    """
    models_svc = request.app.state.models_service
    return models_svc.predict_ablate(body.text, body.remove)


@router.post("/predict/batch", response_model=PredictBatchResponse)
async def predict_batch(request: Request, file: UploadFile = File(...)):
    """
    Vectorized batch classification for uploaded CSV files (max 5,000 rows).
    Requires a 'text' or 'tweet_text' column.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV format")
        
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")
        
    text_col = None
    for col in ["text", "tweet_text", "message", "tweet"]:
        if col in df.columns:
            text_col = col
            break
            
    if not text_col:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain a 'text' or 'tweet_text' column."
        )
        
    raw_texts = df[text_col].dropna().astype(str).tolist()
    if len(raw_texts) == 0:
        raise HTTPException(status_code=400, detail="CSV contains no text rows")
        
    models_svc = request.app.state.models_service
    return models_svc.predict_batch(raw_texts, max_rows=5000)
