from __future__ import annotations
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from insight_agent.engine import InsightEngine
from insight_agent.models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="InsightAgent API", version="0.1.0")
engine = InsightEngine()


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest = Body(...)) -> AnalyzeResponse:  # type: ignore
    try:
        result = engine.analyze(payload)
        return AnalyzeResponse(ok=True, result=result)
    except Exception as e:  # pragma: no cover
        return AnalyzeResponse(ok=False, error=str(e))


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"ok": True})
