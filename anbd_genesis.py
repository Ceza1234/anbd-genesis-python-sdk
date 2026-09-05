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


class AnbdGenesisClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0) -> None:
        if not api_key:
            raise ValueError("api_key é obrigatório.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "anbd-genesis-python-sdk/1.0",
        })

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise AnbdGenesisError(f"Falha de rede ao chamar {path}: {exc}") from exc
        if resp.status_code >= 400:
            try:
                body = resp.json()
                detail = body.get("detail", resp.text)
            except ValueError:
                body = {}
                detail = resp.text
            raise AnbdGenesisAPIError(resp.status_code, detail, body)
        return resp

    def decide(self, input_text: str, reward_feedback: Optional[float] = None) -> Decision:
        payload: Dict[str, Any] = {"input_text": input_text}
        if reward_feedback is not None:
            payload["reward_feedback"] = reward_feedback
        resp = self._request("POST", "/v1/decide", data=json.dumps(payload))
        return Decision._from_api(resp.json())

    def send_feedback(self, decision_id: str, reward: float, input_text: str) -> Decision:
        return self.decide(input_text=input_text, reward_feedback=reward)

    def get_usage(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/me/usage").json()

    def get_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._request("GET", "/v1/me/decisions", params={"limit": limit}).json()

    def export_decisions_csv(self, limit: int = 1000) -> bytes:
        resp = self._request("GET", "/v1/me/decisions/export", params={"limit": limit})
        return resp.content

    def get_billing_portal_url(self) -> str:
        return self._request("POST", "/v1/me/billing-portal").json()["url"]

    def set_webhook(self, webhook_url: str) -> Dict[str, str]:
        return self._request("POST", "/v1/me/webhook", data=json.dumps({"webhook_url": webhook_url})).json()

    def get_webhook_status(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/me/webhook").json()

    def delete_webhook(self) -> None:
        self._request("DELETE", "/v1/me/webhook")

    @staticmethod
    def verify_webhook_signature(secret: str, raw_body: bytes, signature_header: str) -> bool:
        import hashlib
        import hmac
        if not signature_header.startswith("sha256="):
            return False
        expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        received = signature_header.split("=", 1)[1]
        return hmac.compare_digest(expected, received)


def signup(name: str, base_url: str = DEFAULT_BASE_URL) -> Dict[str, str]:
    resp = requests.post(
        f"{base_url.rstrip('/')}/v1/signup",
        json={"name": name, "accepted_terms": True},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
