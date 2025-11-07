from __future__ import annotations
from typing import List
from ..models import RowMetrics, Insight
from .base import BaseAgent


class FatigueAgent(BaseAgent):
    name = "fatigue_agent"

    def __init__(self, frequency_threshold: float = 3.0, ctr_drop_warn_pct: float = 20.0):
        self.frequency_threshold = frequency_threshold
        self.ctr_drop_warn_pct = ctr_drop_warn_pct

    def analyze(self, rows: List[RowMetrics]) -> List[Insight]:
        insights: List[Insight] = []
        for r in rows:
            # Flag creative fatigue
            if (r.frequency is not None and r.frequency >= self.frequency_threshold) and (
                r.ctr_drop_vs_prev7 is not None and r.ctr_drop_vs_prev7 >= self.ctr_drop_warn_pct
            ):
                insights.append(
                    Insight(
                        id=f"fatigue-{r.ad_id or r.ad_name}",
                        scope="ad",
                        keys={"ad_id": r.ad_id, "ad_name": r.ad_name},
                        action="test",
                        title="Likely creative fatigue",
                        rationale=(
                            f"Frequency {r.frequency:.1f} with CTR drop {r.ctr_drop_vs_prev7:.0f}% vs prev7 suggests fatigue."
                        ),
                        recommendations=[
                            "Rotate in fresh creatives",
                            "Narrow targeting or cap frequency",
                        ],
                        severity="medium",
                    )
                )
        return insights
