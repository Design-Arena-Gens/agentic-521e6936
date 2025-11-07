from __future__ import annotations
from typing import Any, Dict, List, Optional
import csv
import io

try:
    # optional at runtime
    from langgraph.graph import Graph
except Exception:  # pragma: no cover
    Graph = None  # type: ignore

from .models import (
    AnalysisConfig,
    AnalysisResult,
    ColumnMapping,
    RowMetrics,
    Insight,
    AnalyzeRequest,
)
from .column_mapper import map_columns
from .agents.ctr_agent import CTRAgent
from .agents.roas_agent import ROASAgent
from .agents.conversion_agent import ConversionAgent
from .agents.fatigue_agent import FatigueAgent
from .llm import summarize_insights


CANONICAL_KEYS = {
    "campaign",
    "ad_set",
    "ad_name",
    "ad_id",
    "spend",
    "impressions",
    "clicks",
    "ctr",
    "frequency",
    "roas",
    "purchases",
    "purchase_value",
    "adds_to_cart",
    "atc_to_purchase_pct",
    "ctr_7d",
    "ctr_prev7",
    "ctr_drop_vs_prev7",
}


class InsightEngine:
    def __init__(self, config: Optional[AnalysisConfig] = None) -> None:
        self.config = config or AnalysisConfig()
        self.agents = [
            CTRAgent(healthy_ctr_pct=self.config.ctr_healthy_pct),
            ROASAgent(),
            ConversionAgent(atc_to_purchase_min_pct=self.config.atc_to_purchase_min_pct),
            FatigueAgent(
                frequency_threshold=self.config.frequency_fatigue_threshold,
                ctr_drop_warn_pct=self.config.ctr_drop_warn_pct,
            ),
        ]

        self.graph = None
        if Graph is not None:
            try:
                g = Graph()
                for a in self.agents:
                    g.add_node(a.name, a.analyze)
                # simple linear flow
                for i in range(len(self.agents) - 1):
                    g.add_edge(self.agents[i].name, self.agents[i + 1].name)
                self.graph = g
            except Exception:
                self.graph = None

    # Public API
    def analyze(self, payload: Dict[str, Any] | AnalyzeRequest) -> AnalysisResult:
        req = payload if isinstance(payload, AnalyzeRequest) else AnalyzeRequest(**payload)
        cfg = req.config or self.config

        columns, rows = self._parse_input(req)
        mapping = map_columns(columns)
        records = self._rows_to_metrics(rows, mapping)

        insights: List[Insight] = []
        if self.graph is not None:
            # Exec each node sequentially; collect
            current_rows = records
            for agent in self.agents:
                agent_insights = agent.analyze(current_rows)
                insights.extend(agent_insights)
        else:
            for agent in self.agents:
                insights.extend(agent.analyze(records))

        if cfg.llm_enabled:
            summary = summarize_insights(insights, model=cfg.openai_model, temperature=cfg.temperature)
        else:
            summary = summarize_insights(insights, model=cfg.openai_model, temperature=0.0)

        return AnalysisResult(column_mapping=mapping, insights=insights[: cfg.max_insights], summary=summary)

    # Helpers
    def _parse_input(self, req: AnalyzeRequest) -> tuple[list[str], list[list[Any]]]:
        if req.csv:
            f = io.StringIO(req.csv)
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                raise ValueError("CSV provided but empty")
            return rows[0], rows[1:]
        if req.columns is not None and req.rows is not None:
            return req.columns, req.rows
        raise ValueError("Provide either csv or columns+rows")

    def _rows_to_metrics(self, rows: List[List[Any]], mapping: ColumnMapping) -> List[RowMetrics]:
        # Build reverse lookup input_col -> canonical
        input_to_canonical: Dict[str, str] = {v: k for k, v in mapping.resolved.items()}

        metrics_rows: List[RowMetrics] = []
        # map input columns to indices
        headers = list(mapping.resolved.values())
        idx = {col: i for i, col in enumerate(headers)}

        for raw in rows:
            values_by_key: Dict[str, Any] = {}
            for canonical, input_name in mapping.resolved.items():
                i = idx.get(input_name)
                if i is None or i >= len(raw):
                    continue
                values_by_key[canonical] = raw[i]

            # Parse numeric fields robustly
            def num(x: Any) -> Optional[float]:
                if x is None:
                    return None
                if isinstance(x, (int, float)):
                    return float(x)
                try:
                    s = str(x).replace(",", "").replace("%", "").strip()
                    if s == "":
                        return None
                    return float(s)
                except Exception:
                    return None

            rm = RowMetrics(
                campaign=self._str(values_by_key.get("campaign")),
                ad_set=self._str(values_by_key.get("ad_set")),
                ad_name=self._str(values_by_key.get("ad_name")),
                ad_id=self._str(values_by_key.get("ad_id")),
                spend=num(values_by_key.get("spend")),
                impressions=int(num(values_by_key.get("impressions") or 0) or 0) if values_by_key.get("impressions") is not None else None,
                clicks=int(num(values_by_key.get("clicks") or 0) or 0) if values_by_key.get("clicks") is not None else None,
                ctr=num(values_by_key.get("ctr")),
                frequency=num(values_by_key.get("frequency")),
                roas=num(values_by_key.get("roas")),
                purchases=int(num(values_by_key.get("purchases") or 0) or 0) if values_by_key.get("purchases") is not None else None,
                purchase_value=num(values_by_key.get("purchase_value")),
                adds_to_cart=int(num(values_by_key.get("adds_to_cart") or 0) or 0) if values_by_key.get("adds_to_cart") is not None else None,
                atc_to_purchase_pct=num(values_by_key.get("atc_to_purchase_pct")),
                ctr_7d=num(values_by_key.get("ctr_7d")),
                ctr_prev7=num(values_by_key.get("ctr_prev7")),
                ctr_drop_vs_prev7=num(values_by_key.get("ctr_drop_vs_prev7")),
            )

            # Derive metrics if missing
            if rm.ctr is None and rm.clicks is not None and rm.impressions:
                rm.ctr = (rm.clicks / max(rm.impressions, 1)) * 100.0
            if rm.roas is None and rm.purchase_value is not None and rm.spend:
                if rm.spend > 0:
                    rm.roas = rm.purchase_value / rm.spend
            if rm.atc_to_purchase_pct is None and rm.purchases is not None and rm.adds_to_cart:
                if rm.adds_to_cart > 0:
                    rm.atc_to_purchase_pct = (rm.purchases / rm.adds_to_cart) * 100.0
            if rm.ctr_drop_vs_prev7 is None and rm.ctr_7d is not None and rm.ctr_prev7 is not None and rm.ctr_prev7 > 0:
                drop = ((rm.ctr_prev7 - rm.ctr_7d) / rm.ctr_prev7) * 100.0
                rm.ctr_drop_vs_prev7 = max(0.0, drop)

            metrics_rows.append(rm)

        return metrics_rows

    def _str(self, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None
