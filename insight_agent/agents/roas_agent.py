from __future__ import annotations
from typing import List
from ..models import RowMetrics, Insight
from .base import BaseAgent


class ROASAgent(BaseAgent):
    name = "roas_agent"

    def analyze(self, rows: List[RowMetrics]) -> List[Insight]:
        insights: List[Insight] = []
        for r in rows:
            if r.roas is None:
                continue
            if 1.0 <= r.roas < 2.0:
                insights.append(
                    Insight(
                        id=f"roas-1-2-{r.ad_id or r.ad_name}",
                        scope="ad",
                        keys={"ad_id": r.ad_id, "ad_name": r.ad_name},
                        action="test",
                        title="ROAS between 1?2",
                        rationale=f"ROAS is {r.roas:.2f} (needs improvement).",
                        recommendations=[
                            "Test 2?3 new hooks/thumbnails",
                            "Rotate a fresh ad variant",
                            "Cap frequency to reduce fatigue",
                        ],
                        severity="medium",
                    )
                )
            elif r.roas < 1.0:
                insights.append(
                    Insight(
                        id=f"roas-sub1-{r.ad_id or r.ad_name}",
                        scope="ad",
                        keys={"ad_id": r.ad_id, "ad_name": r.ad_name},
                        action="pause",
                        title="ROAS < 1",
                        rationale=f"ROAS {r.roas:.2f} is unprofitable.",
                        recommendations=[
                            "Pause or cut spend",
                            "Rebuild creatives and landing match",
                        ],
                        severity="high",
                    )
                )
            else:
                insights.append(
                    Insight(
                        id=f"roas-strong-{r.ad_id or r.ad_name}",
                        scope="ad",
                        keys={"ad_id": r.ad_id, "ad_name": r.ad_name},
                        action="keep",
                        title="ROAS healthy",
                        rationale=f"ROAS {r.roas:.2f} is strong.",
                        recommendations=[
                            "Maintain budget; consider incremental scale",
                        ],
                        severity="low",
                    )
                )
        return insights
