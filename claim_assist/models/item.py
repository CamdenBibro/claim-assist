from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class Complexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Condition(str, Enum):
    NEW = "new"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class ClaimItem:
    """Represents an item in an insurance claim"""
    description: str
    brand: Optional[str] = None
    condition: Optional[str] = None
    age: Optional[str] = None
    features: Optional[str] = None
    estimated_value: Optional[float] = None

    def to_dict(self):
        """Convert to dictionary for API calls"""
        return {
            "description": self.description,
            "brand": self.brand or "unknown",
            "condition": self.condition or "unknown",
            "age": self.age or "unknown",
            "features": self.features or "standard",
            "estimated_value": self.estimated_value
        }


@dataclass
class PricingResult:
    """Results from pricing research and validation"""
    item: str
    recommended_value: float
    percentile_75: Optional[float] = None
    price_range: Optional[str] = None
    confidence: str = Confidence.MEDIUM
    needs_human_review: bool = False
    reasoning: str = ""
    comparable_count: int = 0
    sources: Optional[List[str]] = None
    search_queries_used: Optional[List[str]] = None
    price_source_details: Optional[List[str]] = None

    def to_dict(self):
        """Convert to dictionary for export"""
        return {
            "item": self.item,
            "recommended_value": self.recommended_value,
            "percentile_75": self.percentile_75,
            "price_range": self.price_range,
            "confidence": self.confidence,
            "needs_human_review": self.needs_human_review,
            "reasoning": self.reasoning,
            "comparable_count": self.comparable_count,
            "price_sources": "; ".join(self.price_source_details) if self.price_source_details else "",
            "search_queries": ", ".join(self.search_queries_used) if self.search_queries_used else ""
        }
