from __future__ import annotations
from typing import List
from ..models import RowMetrics, Insight
from .base import BaseAgent


class ConversionAgent(BaseAgent):
    name = "conversion_agent"

    def __init__(self, atc_to_purchase_min_pct: float = 20.0):
        self.atc_to_purchase_min_pct = atc_to_purchase_min_pct

    def analyze(self, rows: List[RowMetrics]) -> List[Insight]:
        insights: List[Insight] = []
        for r in rows:
            if r.atc_to_purchase_pct is None:
                continue
            if r.atc_to_purchase_pct < self.atc_to_purchase_min_pct:
                insights.append(
                    Insight(
                        id=f"conv-drop-{r.ad_id or r.ad_name}",
                        scope="ad",
                        keys={"ad_id": r.ad_id, "ad_name": r.ad_name},
                        action="fix",
                        title="Low ATC?Purchase conversion",
                        rationale=f"ATC?Purchase {r.atc_to_purchase_pct:.1f}% below {self.atc_to_purchase_min_pct:.0f}% benchmark.",
                        recommendations=[
                            "Audit landing and checkout",
                            "Improve load speed and trust signals",
                            "Clarify pricing, shipping, returns",
                        ],
                        severity="high",
                    )
                )
        return insights
