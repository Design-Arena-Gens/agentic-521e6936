from __future__ import annotations
from typing import List
from ..models import RowMetrics, Insight
from .base import BaseAgent


class CTRAgent(BaseAgent):
    name = "ctr_agent"

    def __init__(self, healthy_ctr_pct: float = 1.0):
        self.healthy_ctr_pct = healthy_ctr_pct

    def analyze(self, rows: List[RowMetrics]) -> List[Insight]:
        insights: List[Insight] = []
        for r in rows:
            if r.ctr is None or r.impressions is None:
                continue
            if r.ctr >= self.healthy_ctr_pct:
                # Healthy CTR
                if r.atc_to_purchase_pct is not None and r.atc_to_purchase_pct < 20.0:
                    insights.append(
                        Insight(
                            id=f"ctr-ok-conv-poor-{r.ad_id or r.ad_name}",
                            scope="ad",
                            keys={"ad_id": r.ad_id, "ad_name": r.ad_name},
                            action="fix",
                            title="CTR healthy but conversion weak",
                            rationale=f"CTR {r.ctr:.2f}% is healthy but ATC?Purchase {r.atc_to_purchase_pct or 0:.1f}% is low.",
                            recommendations=[
                                "Audit landing page and checkout",
                                "Test simpler forms and trust signals",
                            ],
                            severity="medium",
                        )
                    )
            else:
                # Weak CTR
                insights.append(
                    Insight(
                        id=f"ctr-weak-{r.ad_id or r.ad_name}",
                        scope="ad",
                        keys={"ad_id": r.ad_id, "ad_name": r.ad_name},
                        action="test",
                        title="Weak CTR",
                        rationale=f"CTR {r.ctr:.2f}% is below healthy threshold {self.healthy_ctr_pct:.2f}%.",
                        recommendations=[
                            "Test 2?3 new hooks and thumbnails",
                            "Refresh headline and primary text",
                        ],
                        severity="medium",
                    )
                )
        return insights
