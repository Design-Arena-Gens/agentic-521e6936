from __future__ import annotations
from typing import List
from ..models import RowMetrics, Insight


class BaseAgent:
    name: str = "base"

    def analyze(self, rows: List[RowMetrics]) -> List[Insight]:
        raise NotImplementedError
