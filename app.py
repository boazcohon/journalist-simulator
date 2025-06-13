import streamlit as st
import os
from dotenv import load_dotenv
from src.personas import list_journalists, load_journalist
from src.evaluation import calculate_response_likelihood

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(
        page_title="PR Training Bot",
        page_icon="📰",
        layout="wide"
    )
    
    st.title("📰 PR Training Bot")
    st.subheader("Practice your pitches with AI journalists")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        mode = st.radio(
            "Choose Mode:",
            ["Pitch Evaluator", "Select Journalist", "Conversation Mode"]
        )
        
        # Journalist selector (always visible)
        st.header("Select Journalist")
        journalists = list_journalists()
        
        if journalists:
            selected_journalist_id = st.selectbox(
                "Choose a journalist:",
                journalists,
                format_func=lambda x: load_journalist(x)["name"] + " (" + load_journalist(x)["publication"] + ")"
            )
            
            # Store selected journalist in session state
            st.session_state.selected_journalist = selected_journalist_id
        else:
            st.warning("No journalists found. Please create one first.")
            st.session_state.selected_journalist = None
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        st.stop()
    
    # Main content based on selected mode
    if mode == "Pitch Evaluator":
        show_pitch_evaluator()
    elif mode == "Select Journalist":
        show_journalist_selection()
    elif mode == "Conversation Mode":
        show_conversation_mode()

def show_journalist_selection():
    st.header("Journalist Profile")
    
    if not hasattr(st.session_state, 'selected_journalist') or st.session_state.selected_journalist is None:
        st.warning("Please select a journalist from the sidebar.")
        return
    
    journalist = load_journalist(st.session_state.selected_journalist)
    
    # Display journalist profile
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📰 Basic Info")
        st.write(f"**Name:** {journalist['name']}")
        st.write(f"**Publication:** {journalist['publication']}")
        st.write(f"**Beat:** {journalist['beat']}")
        st.write(f"**Base Response Rate:** {journalist['base_response_rate']:.1%}")
    
    with col2:
        st.subheader("🔍 Keywords")
        keywords = journalist.get('keyword_triggers', [])
        if keywords:
            for keyword in keywords[:10]:  # Show first 10
                st.code(keyword)
        else:
            st.write("No keywords defined")
    
    # Response factors
    st.subheader("📊 Response Factors")
    factors = journalist.get('response_factors', {})
    
    for category, category_factors in factors.items():
        st.write(f"**{category.title()}:**")
        for factor, multiplier in category_factors.items():
            st.write(f"  • {factor.replace('_', ' ').title()}: {multiplier}x")
    
    # System prompt preview
    with st.expander("🤖 System Prompt Preview"):
        st.write(journalist.get('system_prompt', 'No system prompt defined'))

def show_pitch_evaluator():
    st.header("Pitch Evaluator")
    
    if not hasattr(st.session_state, 'selected_journalist') or st.session_state.selected_journalist is None:
        st.warning("Please select a journalist from the sidebar first.")
        return
    
    journalist = load_journalist(st.session_state.selected_journalist)
    
    # Show selected journalist
    st.info(f"Evaluating pitch for **{journalist['name']}** at **{journalist['publication']}** ({journalist['beat']})")
    
    # Pitch input
    pitch = st.text_area(
        "Enter your pitch:",
        placeholder="Hi [Journalist Name],\n\nI wanted to reach out about...",
        height=200
    )
    
    if st.button("Evaluate Pitch", type="primary"):
        if pitch.strip():
            # Calculate response likelihood
            likelihood = calculate_response_likelihood(pitch, journalist)
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Response Likelihood")
                
                # Progress bar with color coding
                if likelihood >= 0.7:
                    color = "green"
                    emoji = "🟢"
                elif likelihood >= 0.4:
                    color = "orange" 
                    emoji = "🟡"
                else:
                    color = "red"
                    emoji = "🔴"
                
                st.metric(
                    label="Likelihood",
                    value=f"{likelihood:.1%}",
                    help="Probability that the journalist will respond to your pitch"
                )
                
                st.progress(likelihood)
                st.write(f"{emoji} **{get_likelihood_assessment(likelihood)}**")
            
            with col2:
                st.subheader("💡 Quick Analysis")
                
                # Analyze pitch factors
                factors_found = analyze_pitch_factors(pitch, journalist)
                
                if factors_found:
                    st.write("**Positive factors detected:**")
                    for factor in factors_found:
                        st.write(f"✅ {factor}")
                else:
                    st.write("No strong positive factors detected.")
                
                # Keyword matches
                keywords = journalist.get('keyword_triggers', [])
                matched_keywords = [kw for kw in keywords if kw.lower() in pitch.lower()]
                
                if matched_keywords:
                    st.write("**Keyword matches:**")
                    for keyword in matched_keywords:
                        st.code(keyword)
            
            # Improvement suggestions
            with st.expander("🚀 Improvement Suggestions"):
                suggestions = get_improvement_suggestions(pitch, journalist, likelihood)
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")
        
        else:
            st.error("Please enter a pitch to evaluate.")


def get_likelihood_assessment(likelihood):
    """Get human-readable assessment of likelihood."""
    if likelihood >= 0.7:
        return "Excellent - High chance of response"
    elif likelihood >= 0.5:
        return "Good - Moderate chance of response"
    elif likelihood >= 0.3:
        return "Fair - Low but possible response"
    else:
        return "Poor - Very unlikely to respond"


def analyze_pitch_factors(pitch, journalist):
    """Analyze which positive factors are present in the pitch."""
    factors = []
    pitch_lower = pitch.lower()
    
    # Check timing factors
    if "exclusive" in pitch_lower:
        factors.append("Exclusive story")
    if "breaking" in pitch_lower:
        factors.append("Breaking news angle")
    if "embargo" in pitch_lower:
        factors.append("Embargoed information")
    
    # Check quality factors
    if any(word in pitch_lower for word in ["data", "study", "research", "survey"]):
        factors.append("Data-driven content")
    if any(word in pitch_lower for word in ["ceo", "founder", "executive"]):
        factors.append("Executive access")
    
    # Check relevance to beat
    beat_terms = ["enterprise", "software", "saas", "b2b", "security", "technology", "startup"]
    if any(term in pitch_lower for term in beat_terms):
        factors.append("On-beat relevance")
    
    return factors


def get_improvement_suggestions(pitch, journalist, likelihood):
    """Generate improvement suggestions based on pitch analysis."""
    suggestions = []
    pitch_lower = pitch.lower()
    
    if likelihood < 0.3:
        suggestions.append("Consider if this story is relevant to the journalist's beat")
        suggestions.append("Add more compelling news value (exclusivity, timing, impact)")
    
    if "exclusive" not in pitch_lower and likelihood < 0.6:
        suggestions.append("Consider offering exclusive access or first look")
    
    if not any(word in pitch_lower for word in ["data", "study", "research"]):
        suggestions.append("Include data or research to support your story")
    
    if journalist['name'].lower() not in pitch_lower and 'name' not in pitch_lower:
        suggestions.append("Personalize the pitch with the journalist's name")
    
    keywords = journalist.get('keyword_triggers', [])
    matched_keywords = [kw for kw in keywords if kw.lower() in pitch_lower]
    if not matched_keywords:
        suggestions.append(f"Consider including relevant keywords: {', '.join(keywords[:3])}")
    
    if len(pitch.split()) > 150:
        suggestions.append("Consider shortening your pitch - journalists prefer concise messages")
    
    return suggestions

def show_conversation_mode():
    st.header("Conversation with Journalist")
    
    # Placeholder for conversation mode
    st.info("🚧 Conversation mode coming soon!")
    st.write("This section will allow you to:")
    st.write("- Chat in real-time with AI journalists")
    st.write("- Practice follow-up questions")
    st.write("- Build rapport and refine your approach")

if __name__ == "__main__":
    main()