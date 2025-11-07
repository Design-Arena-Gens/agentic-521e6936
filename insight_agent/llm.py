from __future__ import annotations
from typing import List
import os

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from .models import Insight


def summarize_insights(insights: List[Insight], model: str = "gpt-4o-mini", temperature: float = 0.2) -> str:
    if not insights:
        return "No significant insights."

    if OpenAI is None or os.getenv("OPENAI_API_KEY") is None:
        # Deterministic fallback
        actions = {}
        for i in insights:
            actions[i.action] = actions.get(i.action, 0) + 1
        parts = [f"{len(insights)} insights."] + [f"{k}: {v}" for k, v in actions.items()]
        return " ".join(parts)

    client = OpenAI()
    bullet_lines = [f"- [{i.action.upper()}] {i.title}: {i.rationale}" for i in insights[:50]]
    prompt = (
        "Summarize these marketing insights into 2-3 concise sentences, focusing on actions and risk.\n" 
        + "\n".join(bullet_lines)
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or "Summary unavailable"
