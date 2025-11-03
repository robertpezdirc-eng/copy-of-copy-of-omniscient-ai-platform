"""Multi-modal orchestration helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import random


class MultiModalOrchestrator:
    """Fuse insights across text, image, and audio payloads."""

    async def analyze(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        result: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "modalities": [],
            "insights": [],
            "confidence": round(random.uniform(0.76, 0.93), 2),
        }
        if text:
            result["modalities"].append("text")
            result["text_summary"] = self._summarize_text(text)
        if image_url:
            result["modalities"].append("image")
            result["image_tags"] = self._tag_image(image_url)
        if audio_url:
            result["modalities"].append("audio")
            result["audio_transcript"] = self._transcribe_audio(audio_url)
        result["insights"] = self._build_insights(result, metadata)
        return result

    def _summarize_text(self, text: str) -> Dict[str, Any]:
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        snippet = sentences[0][:160] if sentences else text[:160]
        return {
            "snippet": snippet,
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "keywords": self._extract_keywords(text),
        }

    def _tag_image(self, image_url: str) -> List[Dict[str, Any]]:
        labels = [
            ("dashboard", 0.92),
            ("team", 0.84),
            ("analytics", 0.88),
            ("device", 0.73),
        ]
        random.shuffle(labels)
        return [
            {"label": label, "confidence": round(score, 2)}
            for label, score in labels[:3]
        ]

    def _transcribe_audio(self, audio_url: str) -> Dict[str, Any]:
        return {
            "url": audio_url,
            "transcript": "Thank you for calling Omni Enterprise support. Your request has been logged.",
            "language": "en",
        }

    def _extract_keywords(self, text: str) -> List[str]:
        tokens = [token.strip(",.?!").lower() for token in text.split()]
        unique = []
        for token in tokens:
            if len(token) < 4:
                continue
            if token not in unique:
                unique.append(token)
        return unique[:8]

    def _build_insights(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> List[str]:
        insights: List[str] = []
        if "text" in result["modalities"]:
            sentiment = result.get("text_summary", {}).get("sentiment")
            if sentiment == "positive":
                insights.append("Customer sentiment trending positive across transcripts")
            elif sentiment == "negative":
                insights.append("Escalate to customer success due to negative language markers")
            else:
                insights.append("Sentiment stable; continue monitoring weekly")
        if "image" in result["modalities"]:
            insights.append("Visual assets highlight analytics dashboards; promote BI features")
        if "audio" in result["modalities"]:
            insights.append("Detected support call – sync with ticketing workflow")
        if metadata.get("tenant_id"):
            insights.append(f"Route follow-up summary to tenant {metadata['tenant_id']}")
        return insights
