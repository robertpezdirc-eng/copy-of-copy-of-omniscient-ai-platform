"""
Natural Language Processing Service
Provides NLP capabilities including sentiment analysis, entity extraction, text classification, and summarization.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class NLPService:
    """Service for natural language processing tasks"""
    
    def __init__(self):
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "nl", "pl", "cs", "sl",
            "zh", "ja", "ko", "ar", "ru", "hi", "tr", "sv", "da", "no"
        ]
    
    async def analyze_sentiment(self, tenant_id: str, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            tenant_id: Tenant identifier
            text: Text to analyze
            language: Language code
            
        Returns:
            Sentiment analysis results with score and label
        """
        # Simplified sentiment analysis (in production, use actual NLP models)
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "best"]
        negative_words = ["bad", "terrible", "awful", "horrible", "worst", "hate", "poor", "disappointing"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(0.5 + (positive_count * 0.1), 1.0)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(0.5 - (negative_count * 0.1), 0.0)
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "tenant_id": tenant_id,
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentiment": sentiment,
            "score": round(score, 3),
            "confidence": round(abs(score - 0.5) * 2, 3),
            "language": language,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    async def extract_entities(self, tenant_id: str, text: str) -> Dict[str, Any]:
        """
        Extract named entities from text
        
        Args:
            tenant_id: Tenant identifier
            text: Text to analyze
            
        Returns:
            Extracted entities (people, organizations, locations, dates)
        """
        # Simplified entity extraction (in production, use NER models)
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "emails": [],
            "phone_numbers": []
        }
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities["emails"] = re.findall(email_pattern, text)
        
        # Extract phone numbers (simple pattern)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        entities["phone_numbers"] = re.findall(phone_pattern, text)
        
        # Extract dates (simple pattern)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        entities["dates"] = re.findall(date_pattern, text)
        
        # Capitalized words (potential names/organizations)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        if capitalized_words:
            entities["persons"] = capitalized_words[:5]  # First 5 as potential names
        
        return {
            "tenant_id": tenant_id,
            "text_length": len(text),
            "entities": entities,
            "total_entities": sum(len(v) for v in entities.values()),
            "extracted_at": datetime.utcnow().isoformat()
        }
    
    async def classify_text(self, tenant_id: str, text: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Classify text into predefined categories
        
        Args:
            tenant_id: Tenant identifier
            text: Text to classify
            categories: Optional list of categories to classify into
            
        Returns:
            Classification results with category and confidence
        """
        # Default categories
        if not categories:
            categories = [
                "business", "technology", "sports", "entertainment",
                "politics", "health", "science", "education"
            ]
        
        # Simplified classification using keyword matching
        category_keywords = {
            "business": ["company", "market", "finance", "economy", "revenue", "profit"],
            "technology": ["software", "computer", "ai", "digital", "tech", "innovation"],
            "sports": ["game", "player", "team", "match", "championship", "tournament"],
            "entertainment": ["movie", "music", "celebrity", "show", "film", "actor"],
            "politics": ["government", "election", "policy", "president", "parliament"],
            "health": ["medical", "doctor", "patient", "health", "treatment", "disease"],
            "science": ["research", "study", "discovery", "experiment", "scientist"],
            "education": ["school", "student", "teacher", "university", "learning"]
        }
        
        text_lower = text.lower()
        scores = {}
        
        for category in categories:
            if category in category_keywords:
                keywords = category_keywords[category]
                score = sum(1 for keyword in keywords if keyword in text_lower)
                scores[category] = score
        
        # Get top category
        if scores:
            top_category = max(scores, key=scores.get)
            max_score = scores[top_category]
            total_score = sum(scores.values())
            confidence = max_score / total_score if total_score > 0 else 0
        else:
            top_category = "unknown"
            confidence = 0
        
        return {
            "tenant_id": tenant_id,
            "text_length": len(text),
            "category": top_category,
            "confidence": round(confidence, 3),
            "all_scores": scores,
            "classified_at": datetime.utcnow().isoformat()
        }
    
    async def summarize_text(self, tenant_id: str, text: str, max_sentences: int = 3) -> Dict[str, Any]:
        """
        Summarize text by extracting key sentences
        
        Args:
            tenant_id: Tenant identifier
            text: Text to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Text summary
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            summary = text
        else:
            # Simple extractive summarization - take first, middle, and last sentences
            indices = [0, len(sentences) // 2, len(sentences) - 1]
            summary_sentences = [sentences[i] for i in indices[:max_sentences]]
            summary = ". ".join(summary_sentences) + "."
        
        compression_ratio = len(summary) / len(text) if len(text) > 0 else 0
        
        return {
            "tenant_id": tenant_id,
            "original_length": len(text),
            "summary_length": len(summary),
            "summary": summary,
            "compression_ratio": round(compression_ratio, 3),
            "sentences_used": min(max_sentences, len(sentences)),
            "summarized_at": datetime.utcnow().isoformat()
        }
    
    async def detect_language(self, tenant_id: str, text: str) -> Dict[str, Any]:
        """
        Detect the language of text
        
        Args:
            tenant_id: Tenant identifier
            text: Text to analyze
            
        Returns:
            Detected language with confidence
        """
        # Simplified language detection (in production, use actual language detection models)
        # Check for common words in different languages
        language_patterns = {
            "en": ["the", "is", "and", "to", "a", "of", "in"],
            "es": ["el", "la", "de", "que", "y", "en", "los"],
            "fr": ["le", "de", "et", "la", "les", "des", "un"],
            "de": ["der", "die", "und", "in", "den", "von", "zu"],
            "it": ["il", "di", "e", "la", "per", "in", "che"],
            "pt": ["o", "de", "e", "a", "do", "da", "em"]
        }
        
        text_lower = text.lower()
        scores = {}
        
        for lang, patterns in language_patterns.items():
            score = sum(1 for pattern in patterns if f" {pattern} " in f" {text_lower} ")
            scores[lang] = score
        
        if scores:
            detected_lang = max(scores, key=scores.get)
            max_score = scores[detected_lang]
            total_score = sum(scores.values())
            confidence = max_score / total_score if total_score > 0 else 0
        else:
            detected_lang = "unknown"
            confidence = 0
        
        return {
            "tenant_id": tenant_id,
            "detected_language": detected_lang,
            "confidence": round(confidence, 3),
            "all_scores": scores,
            "text_length": len(text),
            "detected_at": datetime.utcnow().isoformat()
        }
    
    async def extract_keywords(self, tenant_id: str, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """
        Extract keywords from text
        
        Args:
            tenant_id: Tenant identifier
            text: Text to analyze
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            Extracted keywords with scores
        """
        # Simplified keyword extraction
        # Remove common stop words
        stop_words = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "but", "in", "with", "to", "for", "of", "as", "by"}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Count frequencies
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = sorted_keywords[:max_keywords]
        
        return {
            "tenant_id": tenant_id,
            "keywords": [{"word": word, "frequency": freq, "score": round(freq / len(words), 3)} for word, freq in top_keywords],
            "total_words": len(words),
            "unique_words": len(word_freq),
            "extracted_at": datetime.utcnow().isoformat()
        }
    
    async def get_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get NLP service usage statistics
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Usage statistics
        """
        return {
            "tenant_id": tenant_id,
            "statistics": {
                "total_analyses": 0,  # Would track actual usage
                "sentiment_analyses": 0,
                "entity_extractions": 0,
                "classifications": 0,
                "summarizations": 0,
                "language_detections": 0,
                "keyword_extractions": 0
            },
            "supported_languages": len(self.supported_languages),
            "generated_at": datetime.utcnow().isoformat()
        }
