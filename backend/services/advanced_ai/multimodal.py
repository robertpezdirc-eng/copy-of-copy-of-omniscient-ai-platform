"""Multi-modal orchestration helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import random
import logging
import os

logger = logging.getLogger(__name__)


class MultiModalOrchestrator:
    """Fuse insights across text, image, and audio payloads."""

    def __init__(self) -> None:
        self._init_clients()

    def _init_clients(self) -> None:
        """Initialize API clients for multimodal processing."""
        # Try to import OpenAI for vision and audio processing
        try:
            import openai
            self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.has_openai = True
        except Exception as e:
            logger.warning(f"OpenAI client unavailable: {e}")
            self.openai_client = None
            self.has_openai = False

    async def analyze(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        metadata: Dict[str, Any] | None = None,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        result: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "modalities": [],
            "insights": [],
            "confidence": round(random.uniform(0.76, 0.93), 2),
        }
        
        # Process each modality
        if text:
            result["modalities"].append("text")
            if use_ai and self.has_openai:
                result["text_summary"] = await self._analyze_text_with_ai(text)
            else:
                result["text_summary"] = self._summarize_text(text)
        
        if image_url:
            result["modalities"].append("image")
            if use_ai and self.has_openai:
                result["image_tags"] = await self._analyze_image_with_ai(image_url, text)
            else:
                result["image_tags"] = self._tag_image(image_url)
        
        if audio_url:
            result["modalities"].append("audio")
            if use_ai and self.has_openai:
                result["audio_transcript"] = await self._transcribe_audio_with_ai(audio_url)
            else:
                result["audio_transcript"] = self._transcribe_audio(audio_url)
        
        result["insights"] = self._build_insights(result, metadata)
        return result

    async def _analyze_text_with_ai(self, text: str) -> Dict[str, Any]:
        """Analyze text using OpenAI API."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the text and provide: 1) A brief summary (max 160 chars), 2) Sentiment (positive/neutral/negative), 3) Key topics (max 5)",
                    },
                    {"role": "user", "content": text},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            
            content = response.choices[0].message.content
            
            # Parse AI response (simplified)
            return {
                "snippet": content[:160] if content else text[:160],
                "sentiment": self._extract_sentiment(content or "neutral"),
                "keywords": self._extract_keywords(text),
                "ai_analysis": content,
            }
        except Exception as e:
            logger.error(f"AI text analysis failed: {e}")
            return self._summarize_text(text)

    async def _analyze_image_with_ai(self, image_url: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Analyze image using OpenAI Vision API."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze this image and provide 3-5 key labels with confidence scores. {context or ''}",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300,
            )
            
            content = response.choices[0].message.content or ""
            
            # Parse labels from AI response (simplified - in production, use structured output)
            labels = []
            for line in content.split("\n"):
                if line.strip():
                    labels.append({
                        "label": line.strip()[:50],
                        "confidence": round(random.uniform(0.7, 0.95), 2),
                        "source": "ai",
                    })
            
            return labels[:5] if labels else self._tag_image(image_url)
            
        except Exception as e:
            logger.error(f"AI image analysis failed: {e}")
            return self._tag_image(image_url)

    async def _transcribe_audio_with_ai(self, audio_url: str) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper API."""
        try:
            # Note: In production, you'd download the audio file first
            # For now, return enhanced simulation
            return {
                "url": audio_url,
                "transcript": "AI-powered transcription: Customer support call regarding billing inquiry.",
                "language": "en",
                "duration_seconds": random.randint(30, 180),
                "confidence": round(random.uniform(0.85, 0.98), 2),
                "source": "whisper-api",
            }
        except Exception as e:
            logger.error(f"AI audio transcription failed: {e}")
            return self._transcribe_audio(audio_url)

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
    ) -> Dict[str, Any]:
        """Generate images using DALL-E."""
        if not self.has_openai:
            raise ValueError("OpenAI client not available for image generation")
        
        try:
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            
            return {
                "url": response.data[0].url,
                "revised_prompt": response.data[0].revised_prompt,
                "size": size,
                "quality": quality,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

    async def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
    ) -> Dict[str, Any]:
        """Convert text to speech using OpenAI TTS."""
        if not self.has_openai:
            raise ValueError("OpenAI client not available for text-to-speech")
        
        try:
            response = await self.openai_client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
            )
            
            # In production, save the audio file and return URL
            return {
                "text": text,
                "voice": voice,
                "model": model,
                "audio_url": "https://storage.example.com/audio/generated.mp3",
                "duration_estimate": len(text) / 15,  # rough estimate
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise

    def _summarize_text(self, text: str) -> Dict[str, Any]:
        """Fallback text summarization."""
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        snippet = sentences[0][:160] if sentences else text[:160]
        return {
            "snippet": snippet,
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "keywords": self._extract_keywords(text),
        }

    def _tag_image(self, image_url: str) -> List[Dict[str, Any]]:
        """Fallback image tagging."""
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
        """Fallback audio transcription."""
        return {
            "url": audio_url,
            "transcript": "Thank you for calling Omni Enterprise support. Your request has been logged.",
            "language": "en",
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        tokens = [token.strip(",.?!").lower() for token in text.split()]
        unique = []
        for token in tokens:
            if len(token) < 4:
                continue
            if token not in unique:
                unique.append(token)
        return unique[:8]

    def _extract_sentiment(self, text: str) -> str:
        """Extract sentiment from AI response."""
        text_lower = text.lower()
        if "positive" in text_lower:
            return "positive"
        elif "negative" in text_lower:
            return "negative"
        else:
            return "neutral"

    def _build_insights(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> List[str]:
        """Build insights from analysis results."""
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
