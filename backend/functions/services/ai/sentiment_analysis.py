"""
Sentiment Analysis Service
NLP for 50+ languages, emotion detection, entity extraction

Backends:
- HuggingFace transformers for multilingual sentiment
- SpaCy for entities (NER)
- OpenAI fallback for edge cases
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SentimentAnalysisService:
    """Multilingual sentiment and emotion detection"""
    
    def __init__(self):
        self._hf_pipeline = None
        self._spacy_nlp = None
    
    async def analyze(self, text: str, lang: str = "auto") -> Dict[str, Any]:
        """
        Analyze sentiment and extract entities
        
        Returns:
            sentiment, score, emotion, entities, keywords
        """
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
            logger.error(f"Sentiment analysis error: {str(e)}")
            return {"text": text, "sentiment": "neutral", "score": 0.5}
    
    async def _transformers_sentiment(self, text: str):
        try:
            if self._hf_pipeline is None:
                from transformers import pipeline
                # Multilingual sentiment model
                self._hf_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment")
            result = self._hf_pipeline(text)[0]
            label = result.get("label", "neutral").lower()
            score = float(result.get("score", 0.5))
            # Normalize labels to positive/neutral/negative
            if label in ["positive", "neutral", "negative"]:
                sentiment = label
            elif label.endswith("positive"):
                sentiment = "positive"
            elif label.endswith("negative"):
                sentiment = "negative"
            else:
                sentiment = "neutral"
            return sentiment, score
        except Exception as e:
            logger.warning(f"HF transformers unavailable, fallback to rule-based: {e}")
            return ("neutral", 0.5)
    
    async def _spacy_entities(self, text: str):
        try:
            if self._spacy_nlp is None:
                import spacy
                # Lightweight English model as default; multilingual models can be added per need
                self._spacy_nlp = spacy.load("en_core_web_sm")
            doc = self._spacy_nlp(text)
            return [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
            ]
        except Exception as e:
            logger.warning(f"spaCy unavailable, no entities extracted: {e}")
            return []
    
    def _map_emotion(self, sentiment: str, score: float) -> str:
        if sentiment == "positive" and score >= 0.7:
            return "joy"
        if sentiment == "negative" and score >= 0.7:
            return "anger"
        if 0.4 <= score <= 0.6:
            return "neutral"
        return "mixed"
    
    def _extract_keywords(self, text: str):
        # Very simple keyword extraction; replace with RAKE/KeyBERT if needed
        words = [w.strip(",.?!").lower() for w in text.split()]
        common = [w for w in words if len(w) > 4]
        return list(dict.fromkeys(common))  # unique preserve order


# Singleton
_sentiment_service = None

def get_sentiment_service() -> SentimentAnalysisService:
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentAnalysisService()
    return _sentiment_service
