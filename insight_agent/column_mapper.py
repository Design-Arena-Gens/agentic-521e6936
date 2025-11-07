from __future__ import annotations
import re
from typing import Dict, List, Tuple
from difflib import get_close_matches
from .models import ColumnSpec, ColumnMapping

CANONICAL_SPECS: List[ColumnSpec] = [
    ColumnSpec(key="campaign", aliases=["campaign name", "campaign", "campaign_title"], required=False),
    ColumnSpec(key="ad_set", aliases=["ad set", "ad set name", "adset", "adset name"], required=False),
    ColumnSpec(key="ad_name", aliases=["ad name", "ad"], required=False),
    ColumnSpec(key="ad_id", aliases=["ad id", "adid", "id"], required=False),

    ColumnSpec(key="spend", aliases=["spend", "cost", "amount_spent"], required=True),
    ColumnSpec(key="impressions", aliases=["impressions", "impr"], required=True),
    ColumnSpec(key="clicks", aliases=["clicks", "link clicks", "click"], required=False),
    ColumnSpec(key="ctr", aliases=["ctr", "ctr %", "click-through rate"], required=False),
    ColumnSpec(key="frequency", aliases=["frequency", "freq"], required=False),
    ColumnSpec(key="roas", aliases=["roas", "return on ad spend"], required=False),

    ColumnSpec(key="purchases", aliases=["purchases", "purchase", "conversions"], required=False),
    ColumnSpec(key="purchase_value", aliases=["purchase value", "revenue", "conversion value"], required=False),
    ColumnSpec(key="adds_to_cart", aliases=["adds to cart", "atc"], required=False),
    ColumnSpec(key="atc_to_purchase_pct", aliases=["atc?purchase %", "atc->purchase %"], required=False),

    ColumnSpec(key="ctr_7d", aliases=["ctr 7d %", "ctr_7d"], required=False),
    ColumnSpec(key="ctr_prev7", aliases=["ctr prev7 %", "ctr_prev7"], required=False),
    ColumnSpec(key="ctr_drop_vs_prev7", aliases=["ctr drop vs prev7 %", "ctr_drop_vs_prev7"], required=False),
]


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\s_\-]+", " ", s)
    s = s.replace("?", "->")
    s = re.sub(r"[^a-z0-9%\-> ]", "", s)
    s = s.replace(" percent", "%")
    return s


auto_vocab: Dict[str, str] = {}
for spec in CANONICAL_SPECS:
    for alias in [spec.key] + spec.aliases:
        auto_vocab[_normalize(alias)] = spec.key


def map_columns(input_columns: List[str]) -> ColumnMapping:
    normalized_to_input: Dict[str, str] = {_normalize(c): c for c in input_columns}

    resolved: Dict[str, str] = {}
    missing: List[str] = []

    for spec in CANONICAL_SPECS:
        # Exact/alias matching first
        matches: List[Tuple[str, str]] = []
        for norm, original in normalized_to_input.items():
            if norm in auto_vocab and auto_vocab[norm] == spec.key:
                matches.append((norm, original))
        if matches:
            resolved[spec.key] = matches[0][1]
            continue

        # Fuzzy matching next
        candidates = list(normalized_to_input.keys())
        possible_aliases = [_normalize(x) for x in ([spec.key] + spec.aliases)]
        suggestion = None
        for alias in possible_aliases:
            close = get_close_matches(alias, candidates, n=1, cutoff=0.86)
            if close:
                suggestion = close[0]
                break
        if suggestion:
            resolved[spec.key] = normalized_to_input[suggestion]
        elif spec.required:
            missing.append(spec.key)

    return ColumnMapping(resolved=resolved, missing=missing)
