"""
SDK oficial em Python para o ANBD-GENESIS — Infraestrutura de Decisão Adaptativa.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

DEFAULT_BASE_URL = "https://anbd-genesis-enterprise.onrender.com"


class AnbdGenesisError(Exception):
    """Erro genérico do SDK."""


class AnbdGenesisAPIError(AnbdGenesisError):
    def __init__(self, status_code: int, detail: str, body: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.detail = detail
        self.body = body or {}
        super().__init__(f"ANBD-GENESIS API error {status_code}: {detail}")


@dataclass
class Decision:
    decision_id: str
    timestamp: str
    action: str
    confidence_level: str
    confidence_score: float
    principal_score: float
    secondary_score: float
    novelty: float
    latency_ms: float
    rationale: List[str]
    oracle_payload: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def _from_api(cls, data: Dict[str, Any]) -> "Decision":
        return cls(
            decision_id=data["decision_id"],
            timestamp=data["timestamp"],
            action=data["action"],
            confidence_level=data["confidence_level"],
            confidence_score=data["confidence_score"],
            principal_score=data["principal_score"],
            secondary_score=data["secondary_score"],
            novelty=data["novelty"],
            latency_ms=data["latency_ms"],
            rationale=data.get("rationale", []),
            oracle_payload=data.get("oracle_payload"),
            raw=data,
        )

    @property
    def needs_human(self) -> bool:
        return self.action in ("ESCALAR", "ABSTER")
