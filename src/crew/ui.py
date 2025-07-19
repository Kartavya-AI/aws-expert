__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
sys.modules["sqlite3.dbapi2"] = sys.modules["pysqlite3.dbapi2"]
import streamlit as st
import os
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import your AWSCrew class
try:
    from awscrew import AWSCrew
    from crewai import Crew, Process
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure 'awscrew' module is available and crewai is installed")
    st.stop()

def load_default_api_keys():
    """Load default API keys from .env file"""
    default_keys = {
        'serper_api_key': os.getenv('SERPER_API_KEY', ''),
        'gemini_api_key': os.getenv('GEMINI_API_KEY', '')
    }
    return default_keys

def set_api_keys():
    """Set API keys as environment variables"""
    api_keys = {}
    
    # Load defaults from .env
    defaults = load_default_api_keys()
    
    # Use user input if provided, otherwise use defaults from .env
    serper_key = st.session_state.get('serper_api_key', '') or defaults['serper_api_key']
    gemini_key = st.session_state.get('gemini_api_key', '') or defaults['gemini_api_key']
    
    if serper_key:
        os.environ['SERPER_API_KEY'] = serper_key
        api_keys['SERPER'] = True
        
    if gemini_key:
        os.environ['GEMINI_API_KEY'] = gemini_key
        os.environ['GOOGLE_API_KEY'] = gemini_key  # Some libraries use GOOGLE_API_KEY
        api_keys['Gemini'] = True
    
    return api_keys

def parse_text_output(response_text):
    """Parse text output from the response (no JSON parsing needed)"""
    try:
        # Clean up the text formatting
        cleaned_text = response_text.strip()
        
        # Remove any summary sections if they exist
        lines = cleaned_text.split('\n')
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            # Skip summary sections
            if 'summary' in line.lower() and ('##' in line or '#' in line):
                skip_section = True
                continue
            elif line.startswith('##') or line.startswith('#'):
                skip_section = False
            
            if not skip_section:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines).strip()
        
    except Exception as e:
        return response_text

def add_note_to_history(content, user_input):
    """Add a note to the history array - extract key points from content"""
    if "notes_history" not in st.session_state:
        st.session_state.notes_history = []
    
    # Extract a brief note from the content (first paragraph or key point)
    lines = content.split('\n')
    note = ""
    
    # Look for the first substantial line that's not a header
    for line in lines:
        clean_line = line.strip()
        if clean_line and not clean_line.startswith('#') and len(clean_line) > 20:
            note = clean_line[:100] + "..." if len(clean_line) > 100 else clean_line
            break
    
    if not note:
        note = f"Query about: {user_input[:50]}..."
    
    current_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.notes_history.append({
        "timestamp": current_time,
        "query": user_input[:50] + "..." if len(user_input) > 50 else user_input,
        "note": note
    })
    """Set API keys as environment variables"""
    api_keys = {}
    
    # Load defaults from .env
    defaults = load_default_api_keys()
    
    # Use user input if provided, otherwise use defaults from .env
    serper_key = st.session_state.get('serper_api_key', '') or defaults['serper_api_key']
    gemini_key = st.session_state.get('gemini_api_key', '') or defaults['gemini_api_key']
    
    if serper_key:
        os.environ['SERPER_API_KEY'] = serper_key
        api_keys['SERPER'] = True
        
    if gemini_key:
        os.environ['GEMINI_API_KEY'] = gemini_key
        os.environ['GOOGLE_API_KEY'] = gemini_key  # Some libraries use GOOGLE_API_KEY
        api_keys['Gemini'] = True
    
    return api_keys

def run_aws_crew(user_input):
    """Run the AWS Crew with user input"""
    try:
        # Create inputs dictionary
        inputs = {
            'topic': user_input,
            'query': user_input  # Some configs might expect 'query'
        }
        
        # Initialize the crew
        crew_instance = AWSCrew()
        
        # Try different approaches to access the crew
        try:
            if hasattr(crew_instance, 'crew'):
                # If crew is a property
                if callable(crew_instance.crew):
                    result = crew_instance.crew().kickoff(inputs=inputs)
                else:
                    result = crew_instance.crew.kickoff(inputs=inputs)
            else:
                # If crew needs to be called as a method
                crew_obj = crew_instance.crew()
                result = crew_obj.kickoff(inputs=inputs)
                
        except AttributeError as e:
            st.warning(f"Standard approach failed: {e}. Trying manual crew creation...")
            
            # Alternative: manually create the crew
            manual_crew = Crew(
                agents=[
                    crew_instance.aws_query_agent(),
                    crew_instance.search_agent(),
                    crew_instance.report_agent()
                ],
                tasks=[
                    crew_instance.aws_query_task(),
                    crew_instance.search_task(),
                    crew_instance.report_task()
                ],
                process=Process.sequential,
                verbose=True
            )
            result = manual_crew.kickoff(inputs=inputs)
        
        return str(result)
        
    except Exception as e:
        error_msg = f"Error running AWS Crew: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg

def main():
    # Page config
    st.set_page_config(
        page_title="AWS Crew Chat",
        page_icon="☁️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better chat appearance
    st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #1e3a8a;
        color: white;
        border-left: 4px solid #3b82f6;
    }
    .assistant-message {
        background-color: #1f2937;
        color: #f9fafb;
        border-left: 4px solid #10b981;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .assistant-message h1, .assistant-message h2, .assistant-message h3 {
        color: #60a5fa;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .assistant-message h1 {
        border-bottom: 2px solid #60a5fa;
        padding-bottom: 0.5rem;
    }
    .assistant-message h2 {
        border-bottom: 1px solid #374151;
        padding-bottom: 0.3rem;
    }
    .assistant-message strong {
        color: #34d399;
    }
    .assistant-message code {
        background-color: #374151;
        color: #fbbf24;
        padding: 0.2rem 0.4rem;
        border-radius: 0.25rem;
        font-family: 'Monaco', 'Consolas', monospace;
    }
    .assistant-message pre {
        background-color: #111827;
        color: #f3f4f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #374151;
        overflow-x: auto;
    }
    .assistant-message ul, .assistant-message ol {
        margin-left: 1rem;
        color: #d1d5db;
    }
    .assistant-message li {
        margin-bottom: 0.3rem;
        line-height: 1.5;
    }
    .message-time {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-top: 0.5rem;
    }
    .stButton > button {
        width: 100%;
    }
    .notes-container {
        background-color: #374151;
        color: #f3f4f6;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-top: 0.5rem;
        font-size: 0.8rem;
    }
    .markdown-content {
        line-height: 1.6;
    }
    .markdown-content p {
        margin-bottom: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("☁️ AWS Crew Chat Assistant")
    st.markdown("Ask questions about AWS services, configurations, and best practices!")
    
    # Sidebar for API configuration
    with st.sidebar:
        st.header("🔑 API Configuration")
        
        # Load default values
        defaults = load_default_api_keys()
        
        # Show default status
        if defaults['serper_api_key'] or defaults['gemini_api_key']:
            st.info("📁 Default keys loaded from .env file")
            with st.expander("View Default Configuration"):
                if defaults['serper_api_key']:
                    st.write(f"• SERPER: ...{defaults['serper_api_key'][-10:]}")
                if defaults['gemini_api_key']:
                    st.write(f"• GEMINI: ...{defaults['gemini_api_key'][-10:]}")
        
        st.markdown("**Override API keys (optional):**")
        st.caption("Leave blank to use .env defaults")
        
        # API Key inputs - only the two you need
        serper_key = st.text_input(
            "SERPER API Key", 
            type="password", 
            key="serper_api_key",
            help="Required for web search functionality. Leave blank to use .env default",
            placeholder="Enter to override .env value"
        )
        
        gemini_key = st.text_input(
            "Gemini API Key", 
            type="password", 
            key="gemini_api_key",
            help="Required for Google Gemini models. Leave blank to use .env default",
            placeholder="Enter to override .env value"
        )
        
        # Show current configuration
        api_keys = set_api_keys()
        st.markdown("---")
        if api_keys:
            st.success("✅ Active Configuration:")
            for api, status in api_keys.items():
                if status:
                    source = "Override" if st.session_state.get(f"{api.lower()}_api_key") else ".env"
                    st.write(f"• {api} ({source})")
        else:
            st.error("❌ No API keys configured!")
            st.warning("Please add keys to .env file or configure above")
        
        # Reset overrides button
        if st.button("🔄 Reset to .env Defaults"):
            st.session_state.serper_api_key = ""
            st.session_state.gemini_api_key = ""
            st.rerun()
        
        # Notes history section
        st.markdown("---")
        st.header("📝 Notes History")
        
        if "notes_history" in st.session_state and st.session_state.notes_history:
            with st.expander(f"📋 View Notes ({len(st.session_state.notes_history)})", expanded=False):
                for i, note in enumerate(reversed(st.session_state.notes_history[-10:])):  # Show last 10
                    st.markdown(f"""
                    <div class="notes-container">
                        <strong>🕒 {note['timestamp']}</strong><br>
                        <em>Q: {note['query']}</em><br>
                        📝 {note['note']}
                    </div>
                    """, unsafe_allow_html=True)
                    
            if st.button("🗑️ Clear Notes"):
                st.session_state.notes_history = []
                st.rerun()
        else:
            st.info("No notes saved yet")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            timestamp = message.get('timestamp', 'Unknown time')
            
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>🙋‍♂️ You:</strong><br>
                    {message['content']}
                    <div class="message-time">🕒 {timestamp}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Use Streamlit's native markdown rendering for better formatting
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #1f2937; color: #f9fafb; padding: 1rem; border-radius: 10px; border-left: 4px solid #10b981; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <strong style="color: #34d399;">🤖 AWS Crew Assistant</strong>
                        <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 1rem;">🕒 {timestamp}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Render the markdown content with Streamlit for proper formatting
                    st.markdown(message['content'])
    
    # Chat input form to handle submissions properly
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask your AWS question:",
                placeholder="e.g., How do I configure S3 bucket policies for security?",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.form_submit_button("Send 📤", type="primary", use_container_width=True)
    
    # Process user input
    if send_button and user_input.strip():
        # Check if at least one API key is configured
        active_keys = set_api_keys()
        if not active_keys:
            st.error("⚠️ Please configure API keys in .env file or override them in the sidebar.")
            st.stop()
        
        # Add user message to chat
        current_time = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input.strip(),
            "timestamp": current_time
        })
        
        # Show thinking spinner and get response
        with st.spinner("🤔 AWS Crew is thinking..."):
            try:
                # Get response from AWS Crew
                raw_response = run_aws_crew(user_input.strip())
                
                # Parse text output (remove summaries, clean formatting)
                cleaned_output = parse_text_output(raw_response)
                
                # Add to notes history
                add_note_to_history(cleaned_output, user_input.strip())
                
                # Add assistant response to chat
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": cleaned_output,
                    "timestamp": current_time
                })
                
            except Exception as e:
                error_response = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_response,
                    "timestamp": current_time
                })
        
        # Rerun to show new messages
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <small>AWS Crew Chat Assistant • Powered by CrewAI</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()