from __future__ import annotations
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict

InsightAction = Literal["pause", "fix", "test", "keep"]


class ColumnSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")
    key: str = Field(..., description="Canonical key (e.g., spend, impressions)")
    aliases: List[str] = Field(default_factory=list)
    required: bool = False
    description: Optional[str] = None


class ColumnMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")
    resolved: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from canonical key -> input column name",
    )
    missing: List[str] = Field(default_factory=list)


class RowMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore")
    campaign: Optional[str] = None
    ad_set: Optional[str] = None
    ad_name: Optional[str] = None
    ad_id: Optional[str] = None

    spend: Optional[float] = None
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr: Optional[float] = Field(None, description="Click-through rate as percentage (0-100)")
    frequency: Optional[float] = None
    roas: Optional[float] = None

    purchases: Optional[int] = None
    purchase_value: Optional[float] = None
    adds_to_cart: Optional[int] = None
    atc_to_purchase_pct: Optional[float] = None

    ctr_7d: Optional[float] = None
    ctr_prev7: Optional[float] = None
    ctr_drop_vs_prev7: Optional[float] = None


class Insight(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    scope: Literal["ad", "ad_set", "campaign", "account"]
    keys: Dict[str, Any] = Field(default_factory=dict)
    action: InsightAction
    title: str
    rationale: str
    recommendations: List[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high"] = "medium"


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    column_mapping: ColumnMapping
    insights: List[Insight]
    summary: Optional[str] = None


class AnalysisConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    llm_enabled: bool = False
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_insights: int = 100
    # thresholds
    ctr_healthy_pct: float = 1.0
    atc_to_purchase_min_pct: float = 20.0
    frequency_fatigue_threshold: float = 3.0
    ctr_drop_warn_pct: float = 20.0


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # Accept either a data frame-like payload or CSV string
    columns: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None
    csv: Optional[str] = None
    config: Optional[AnalysisConfig] = None


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
