from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from parser_refactored import parse_channels

class Filters(BaseModel):
    q: Optional[str] = None
    in_about: Optional[bool] = True
    categories: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    channel_type: Optional[List[str]] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    err_from: Optional[int] = None
    err_to: Optional[int] = None
    er_from: Optional[float] = 1
    er_to: Optional[float] = 10
    male_from: Optional[int] = None
    male_to: Optional[int] = None
    female_from: Optional[int] = None
    female_to: Optional[int] = None
    participants_from: Optional[int] = None
    participants_to: Optional[int] = None
    avg_reach_from: Optional[int] = None
    avg_reach_to: Optional[int] = None
    avg_reach24_from: Optional[int] = None
    avg_reach24_to: Optional[int] = None
    ci_from: Optional[int] = None
    ci_to: Optional[int] = None
    is_verified: Optional[bool] = False
    is_rkn_verified: Optional[bool] = False
    is_stories_available: Optional[bool] = False

class SearchRequest(BaseModel):
    filters: Filters
    channels_quantity: int = 10

app = FastAPI()

@app.post("/channels")
async def get_channels(request: SearchRequest, format: Optional[str] = Query('json')):
    """Retrieve Telegram channels; format can be 'json' or 'csv'"""
    data = parse_channels(request.filters.model_dump(), request.channels_quantity)
    if format.lower() == 'csv':
        df = pd.DataFrame(data)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return StreamingResponse(buf, media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="channels.csv"'})
    return data
