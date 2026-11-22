"""
Vocabulary, Top Predictive Terms, and WordCloud Endpoints
"""

import os
import io
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

from fastapi import APIRouter, Request, HTTPException, Query, Response
from typing import List, Optional
from wordcloud import WordCloud

from rescueai.constants import CATEGORY_CONFIG, CATEGORY_NAMES
from rescueai.api.schemas import ClassTermsResponse

router = APIRouter(tags=["Vocabulary & WordClouds"])

# In-memory wordcloud PNG cache
_WORDCLOUD_CACHE = {}


@router.get("/terms", response_model=List[ClassTermsResponse])
def get_terms(
    request: Request,
    cls: Optional[int] = Query(None, ge=0, le=4)
):
    """
    Returns top predictive n-grams derived from training data using model coefficients.
    """
    models_svc = request.app.state.models_service
    return models_svc.get_top_terms_by_class(cls_idx=cls, top_k=20)


@router.get("/wordcloud/{cls_idx}.png")
def get_wordcloud_image(
    request: Request,
    cls_idx: int
):
    """
    Generates and returns an operations console-themed PNG word cloud
    for category index cls_idx (0..4) using real training vocabulary.
    """
    if cls_idx not in range(5):
        raise HTTPException(status_code=400, detail="Category index must be between 0 and 4")
        
    if cls_idx in _WORDCLOUD_CACHE:
        return Response(content=_WORDCLOUD_CACHE[cls_idx], media_type="image/png")
        
    data_svc = request.app.state.data_service
    df_train = data_svc.df_train
    
    # Filter text for class
    class_df = df_train[df_train["target_label"].astype(int) == cls_idx]
    if class_df.empty:
        raise HTTPException(status_code=404, detail="No training data for this category")
        
    text_corpus = " ".join(class_df["clean_text"].dropna().tolist())
    
    cat_color = CATEGORY_CONFIG[cls_idx]["color"]
    
    # Color function matching category hue
    def custom_color_func(*args, **kwargs):
        return cat_color
        
    wc = WordCloud(
        width=700,
        height=350,
        background_color="#151A21",
        color_func=custom_color_func,
        max_words=80,
        collocations=False
    ).generate(text_corpus)
    
    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    png_bytes = buf.getvalue()
    
    _WORDCLOUD_CACHE[cls_idx] = png_bytes
    return Response(content=png_bytes, media_type="image/png")
