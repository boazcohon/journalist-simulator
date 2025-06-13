import streamlit as st
import os
from dotenv import load_dotenv

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
            ["Select Journalist", "Pitch Evaluator", "Conversation Mode"]
        )
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        st.stop()
    
    # Main content based on selected mode
    if mode == "Select Journalist":
        show_journalist_selection()
    elif mode == "Pitch Evaluator":
        show_pitch_evaluator()
    elif mode == "Conversation Mode":
        show_conversation_mode()

def show_journalist_selection():
    st.header("Select or Create Journalist")
    
    # Placeholder for journalist selection
    st.info("🚧 Journalist selection coming soon!")
    st.write("This section will allow you to:")
    st.write("- Browse existing journalist personas")
    st.write("- Create new journalist personas")
    st.write("- View journalist profiles and response patterns")

def show_pitch_evaluator():
    st.header("Pitch Evaluator")
    
    # Placeholder for pitch evaluation
    st.info("🚧 Pitch evaluator coming soon!")
    st.write("This section will allow you to:")
    st.write("- Submit your pitch for evaluation")
    st.write("- Get detailed feedback on pitch quality")
    st.write("- See response likelihood for different journalists")

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