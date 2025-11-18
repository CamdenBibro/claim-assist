import pytest
from unittest.mock import Mock
from claim_assist.pricing.researcher import PriceResearcher
from claim_assist.models.item import ClaimItem, Complexity


@pytest.fixture
def mock_client():
    """Create mock Anthropic client"""
    return Mock()


@pytest.fixture
def researcher(mock_client):
    """Create PriceResearcher with mock client"""
    return PriceResearcher(mock_client)


def test_research_simple_item(researcher, mock_client):
    """Test research of simple item"""
    mock_response = Mock()
    mock_response.content = [Mock(text='''{
        "comparable_prices": [100, 120, 95, 110, 105],
        "sources": ["eBay", "Amazon", "Best Buy"],
        "recommended_value": 106,
        "confidence": "high",
        "reasoning": "Multiple comparables found",
        "search_queries_used": ["iPhone 13 Pro used"]
    }''')]
    mock_client.messages.create.return_value = mock_response

    item = ClaimItem(description="iPhone 13 Pro", brand="Apple")

    result = researcher.research(item, Complexity.SIMPLE.value)

    assert result['recommended_value'] == 106
    assert len(result['comparable_prices']) == 5
    assert result['confidence'] == 'high'


def test_research_uses_correct_model(researcher, mock_client):
    """Test that complex items use Sonnet model"""
    mock_response = Mock()
    mock_response.content = [Mock(text='''{
        "comparable_prices": [500],
        "sources": ["Etsy"],
        "recommended_value": 500,
        "confidence": "medium",
        "reasoning": "Limited comparables",
        "search_queries_used": []
    }''')]
    mock_client.messages.create.return_value = mock_response

    item = ClaimItem(description="Vintage item")

    # Research complex item
    researcher.research(item, Complexity.COMPLEX.value)

    # Verify Sonnet model was used
    call_args = mock_client.messages.create.call_args
    assert call_args[1]['model'] == researcher.complex_model


def test_research_fallback_on_error(researcher, mock_client):
    """Test fallback when research fails"""
    mock_client.messages.create.side_effect = Exception("API Error")

    item = ClaimItem(description="Test item", estimated_value=100.0)

    result = researcher.research(item, Complexity.SIMPLE.value)

    assert result['recommended_value'] == 100.0
    assert result['confidence'] == 'low'
    assert 'failed' in result['reasoning'].lower()
