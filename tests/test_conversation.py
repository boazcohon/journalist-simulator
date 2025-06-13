import pytest
from src.conversation import ConversationManager
from src.personas import load_journalist


def test_conversation_initialization():
    """Test that conversation manager initializes correctly."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    assert conversation.journalist == journalist
    assert len(conversation.messages) == 0
    assert conversation.total_cost == 0.0
    assert conversation.start_time is not None


def test_add_message():
    """Test adding messages to conversation history."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    conversation.add_message("user", "Hello")
    conversation.add_message("assistant", "Hi there")
    
    assert len(conversation.messages) == 2
    assert conversation.messages[0]["role"] == "user"
    assert conversation.messages[0]["content"] == "Hello"
    assert conversation.messages[1]["role"] == "assistant"
    assert conversation.messages[1]["content"] == "Hi there"
    assert "timestamp" in conversation.messages[0]


def test_conversation_context():
    """Test conversation context building."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    # No context initially
    context = conversation.get_conversation_context()
    assert "Previous conversation:" in context
    
    # Add some messages
    conversation.add_message("user", "Hello")
    conversation.add_message("assistant", "Hi there")
    
    context = conversation.get_conversation_context()
    assert "Hello" in context
    assert "Hi there" in context


def test_generate_response_integration():
    """Test generating responses with actual API."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    response, cost = conversation.generate_response("Hi Jane, I have a tech story for you")
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert isinstance(cost, float)
    assert cost >= 0
    assert len(conversation.messages) == 2  # User message + assistant response


def test_engagement_assessment():
    """Test engagement level assessment."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    # No engagement initially
    assert conversation.assess_engagement_level() == "No engagement yet"
    
    # Add user message
    conversation.add_message("user", "Hello")
    assert conversation.assess_engagement_level() == "No responses yet"
    
    # Test high interest response
    conversation_high = ConversationManager(journalist)
    conversation_high.add_message("user", "Hello")
    conversation_high.add_message("assistant", "This sounds very interesting, tell me more!")
    engagement_high = conversation_high.assess_engagement_level()
    assert "High Interest" in engagement_high
    
    # Test low interest response
    conversation_low = ConversationManager(journalist)
    conversation_low.add_message("user", "Hello")
    conversation_low.add_message("assistant", "I'm not interested in this story")
    engagement_low = conversation_low.assess_engagement_level()
    assert "Low Interest" in engagement_low
    
    # Test neutral response
    conversation_neutral = ConversationManager(journalist)
    conversation_neutral.add_message("user", "Hello")
    conversation_neutral.add_message("assistant", "Thanks for reaching out")
    engagement_neutral = conversation_neutral.assess_engagement_level()
    assert "Neutral" in engagement_neutral


def test_conversation_summary():
    """Test conversation summary generation."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    conversation.add_message("user", "Hello")
    conversation.add_message("assistant", "Hi there")
    conversation.total_cost = 0.05
    
    summary = conversation.get_conversation_summary()
    
    assert summary["journalist"] == journalist["name"]
    assert summary["publication"] == journalist["publication"]
    assert summary["message_count"] == 2
    assert summary["total_cost"] == 0.05
    assert "duration" in summary
    assert "messages" in summary


def test_conversation_maintains_personality():
    """Test that conversations maintain journalist personality."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    # Test tech-related pitch
    tech_response, _ = conversation.generate_response(
        "Hi Jane, I have exclusive data about enterprise security breaches"
    )
    
    # Response should be relevant to her beat
    assert len(tech_response) > 50  # Should be substantial
    
    # Test off-beat pitch
    conversation2 = ConversationManager(journalist)
    sports_response, _ = conversation2.generate_response(
        "Hi Jane, we have a new sports equipment launch"
    )
    
    # Should be different responses for different relevance levels
    assert tech_response != sports_response


def test_cost_tracking():
    """Test that costs are tracked properly."""
    journalist = load_journalist("jane_smith_techcrunch")
    conversation = ConversationManager(journalist)
    
    initial_cost = conversation.total_cost
    response, cost = conversation.generate_response("Test message")
    
    assert conversation.total_cost > initial_cost
    assert conversation.total_cost == initial_cost + cost
    assert cost > 0  # Should have some cost for API call