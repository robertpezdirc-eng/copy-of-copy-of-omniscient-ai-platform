import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    def __init__(self):
        self._hf_pipeline = None
        self._spacy_nlp = None

    async def analyze(self, text: str) -> Dict[str, Any]:
        try:
            sentiment, score = await self._transformers_sentiment(text)
            entities = await self._spacy_entities(text)
            emotion = self._map_emotion(sentiment, score)
            return {
                "text": text,
                "sentiment": sentiment,
                "score": score,
                "emotion": emotion,
                "entities": entities,
                "keywords": self._extract_keywords(text)
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"text": text, "sentiment": "neutral", "score": 0.5}

    async def _transformers_sentiment(self, text: str):
        try:
            if self._hf_pipeline is None:
                from transformers import pipeline
                self._hf_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment")
            res = self._hf_pipeline(text)[0]
            label = res.get("label", "neutral").lower()
            score = float(res.get("score", 0.5))
            if label.endswith("positive"): sentiment = "positive"
            elif label.endswith("negative"): sentiment = "negative"
            elif label in ("positive", "negative", "neutral"): sentiment = label
            else: sentiment = "neutral"
            return sentiment, score
        except Exception as e:
            logger.warning(f"HF pipeline unavailable: {e}")
            return ("neutral", 0.5)

    async def _spacy_entities(self, text: str):
        try:
            if self._spacy_nlp is None:
                import spacy
                self._spacy_nlp = spacy.load("en_core_web_sm")
            doc = self._spacy_nlp(text)
            return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        except Exception as e:
            logger.warning(f"spaCy unavailable: {e}")
            return []

    def _map_emotion(self, sentiment: str, score: float) -> str:
        if sentiment == "positive" and score >= 0.7: return "joy"
        if sentiment == "negative" and score >= 0.7: return "anger"
        if 0.4 <= score <= 0.6: return "neutral"
        return "mixed"

    def _extract_keywords(self, text: str):
        words = [w.strip(",.?!").lower() for w in text.split()]
        return list(dict.fromkeys([w for w in words if len(w) > 4]))
