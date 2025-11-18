import pytest
from unittest.mock import Mock, MagicMock
from claim_assist.pricing.classifier import ItemClassifier
from claim_assist.models.item import ClaimItem, Complexity


@pytest.fixture
def mock_client():
    """Create mock Anthropic client"""
    client = Mock()
    return client


@pytest.fixture
def classifier(mock_client):
    """Create ItemClassifier with mock client"""
    return ItemClassifier(mock_client)


def test_classify_simple_item(classifier, mock_client):
    """Test classification of simple item"""
    # Setup mock response
    mock_response = Mock()
    mock_response.content = [Mock(text='{"complexity": "simple", "reasoning": "Clear brand and model"}')]
    mock_client.messages.create.return_value = mock_response

    item = ClaimItem(
        description="iPhone 13 Pro",
        brand="Apple",
        condition="good"
    )

    result = classifier.classify(item)

    assert result['complexity'] == Complexity.SIMPLE.value
    assert 'reasoning' in result


def test_classify_complex_item(classifier, mock_client):
    """Test classification of complex item"""
    mock_response = Mock()
    mock_response.content = [Mock(text='{"complexity": "complex", "reasoning": "Vintage item"}')]
    mock_client.messages.create.return_value = mock_response

    item = ClaimItem(
        description="1960s Danish modern credenza",
        brand="Unknown",
        condition="fair"
    )

    result = classifier.classify(item)

    assert result['complexity'] == Complexity.COMPLEX.value


def test_classify_fallback_on_error(classifier, mock_client):
    """Test fallback to moderate on classification error"""
    # Simulate API error
    mock_client.messages.create.side_effect = Exception("API Error")

    item = ClaimItem(description="Test item")

    result = classifier.classify(item)

    assert result['complexity'] == Complexity.MODERATE.value
    assert 'error' in result['reasoning'].lower()
