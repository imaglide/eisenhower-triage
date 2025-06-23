import streamlit as st
import os
from utils.eml_parser import parse_eml
from agent_logic import run_all_triage
from backend.config import Config

# Page configuration
st.set_page_config(
    page_title="Eisenhower Triage Agent",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📧 Eisenhower Triage Agent")
    st.markdown("Upload an email (.eml file) to analyze and triage using multiple AI strategies with real LLM calls.")
    
    # Check configuration status
    show_config_status()
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📎 Upload Email")
        uploaded_file = st.file_uploader(
            "Choose an .eml file",
            type=['eml'],
            help="Select an email file in .eml format"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    # Main content area
    if uploaded_file is not None:
        # Parse the email
        try:
            subject, sender, body = parse_eml(uploaded_file)
            
            # Display parsed content
            st.header("📋 Parsed Email Content")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("From")
                st.info(sender)
                
                st.subheader("Subject")
                st.info(subject)
            
            with col2:
                st.subheader("Body Preview")
                # Show first 500 characters of body
                body_preview = body[:500] + "..." if len(body) > 500 else body
                st.text_area("Email Body", body_preview, height=200, disabled=True)
                
                if len(body) > 500:
                    st.caption(f"Showing first 500 characters of {len(body)} total characters")
            
            # Run triage button
            st.header("🚀 Triage Analysis")
            
            if st.button("Run Triage Analysis", type="primary", use_container_width=True):
                with st.spinner("Running triage analysis with real LLM calls..."):
                    # Run all triage strategies
                    triage_results = run_all_triage(subject, sender, body)
                    
                    # Display results
                    st.success("✅ Triage analysis completed!")
                    
                    # Create tabs for different strategies
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📧 Email Only", 
                        "🔍 Contextual", 
                        "🧠 Embedding", 
                        "🎯 Outcomes"
                    ])
                    
                    with tab1:
                        st.subheader("Email Only Strategy")
                        display_triage_result(triage_results.get('email_only', {}))
                    
                    with tab2:
                        st.subheader("Contextual Strategy")
                        display_triage_result(triage_results.get('contextual', {}))
                    
                    with tab3:
                        st.subheader("Embedding Strategy")
                        display_triage_result(triage_results.get('embedding', {}))
                    
                    with tab4:
                        st.subheader("Outcomes Strategy")
                        display_triage_result(triage_results.get('outcomes', {}))
                    
                    # Summary section
                    st.header("📊 Summary")
                    display_summary(triage_results)
                    
        except Exception as e:
            st.error(f"❌ Error parsing email: {str(e)}")
            st.exception(e)
    
    else:
        # Show instructions when no file is uploaded
        st.info("👆 Please upload an .eml file using the sidebar to get started.")
        
        st.markdown("""
        ### How to use:
        1. **Upload**: Use the sidebar to upload an .eml email file
        2. **Review**: Check the parsed email content
        3. **Analyze**: Click "Run Triage Analysis" to process the email with real LLM calls
        4. **Review Results**: View triage results across 4 different strategies
        
        ### Supported Strategies:
        - **Email Only**: OpenAI GPT-4 analysis of email content
        - **Contextual**: Context-aware analysis using sender profiles from Supabase
        - **Embedding**: Semantic embedding-based analysis using OpenAI embeddings
        - **Outcomes**: Outcome-focused analysis using historical triage data
        
        ### Real AI Features:
        - 🤖 **OpenAI GPT-4** for intelligent email classification
        - 🗄️ **Supabase** for sender profiles and historical data
        - 🔍 **OpenAI Embeddings** for semantic similarity
        - 📊 **Historical Analysis** for outcome prediction
        """)

def show_config_status():
    """Display configuration status in the sidebar"""
    with st.sidebar:
        st.header("⚙️ Configuration Status")
        
        # Check OpenAI
        openai_status = "✅" if Config.OPENAI_API_KEY else "❌"
        st.write(f"{openai_status} OpenAI API Key")
        
        # Check Supabase
        supabase_status = "✅" if Config.SUPABASE_URL and Config.SUPABASE_KEY else "❌"
        st.write(f"{supabase_status} Supabase Connection")
        
        # Show model info
        if Config.OPENAI_API_KEY:
            st.info(f"Model: {Config.OPENAI_MODEL}")
        
        # Show warning if config is incomplete
        if not Config.validate():
            st.warning("⚠️ Some features may not work without proper configuration")
            st.caption("Check your .env file for required API keys")

def display_triage_result(result):
    """Display individual triage strategy results"""
    if not result:
        st.warning("No results available for this strategy")
        return
    
    # Check if this was a real LLM call or fallback
    strategy_type = result.get('metadata', {}).get('strategy', 'unknown')
    is_real_llm = 'real_llm' in strategy_type
    
    # Strategy status indicator
    if is_real_llm:
        st.success("🤖 Real LLM Analysis")
    else:
        st.warning("⚠️ Fallback Analysis (LLM unavailable)")
    
    # Priority quadrant
    if 'priority' in result:
        priority = result['priority']
        priority_colors = {
            'urgent_important': '🔴',
            'important_not_urgent': '🟡', 
            'urgent_not_important': '🟠',
            'not_urgent_not_important': '🟢'
        }
        
        st.metric(
            "Priority Quadrant",
            f"{priority_colors.get(priority, '❓')} {priority.replace('_', ' ').title()}"
        )
    
    # Confidence score
    if 'confidence' in result:
        confidence = result['confidence']
        st.metric("Confidence", f"{confidence:.1%}")
        
        # Progress bar for confidence
        st.progress(confidence)
    
    # Reasoning
    if 'reasoning' in result:
        st.subheader("Reasoning")
        st.write(result['reasoning'])
    
    # Additional metadata
    if 'metadata' in result:
        metadata = result['metadata']
        st.subheader("Technical Details")
        
        # Model information
        if 'model_used' in metadata:
            st.write(f"**Model**: {metadata['model_used']}")
        
        # Token usage
        if 'tokens_used' in metadata and metadata['tokens_used'] > 0:
            st.write(f"**Tokens Used**: {metadata['tokens_used']}")
        
        # Strategy-specific details
        if strategy_type == 'real_llm_contextual':
            if 'sender_profile_found' in metadata:
                st.write(f"**Sender Profile**: {'✅ Found' if metadata['sender_profile_found'] else '❌ Not Found'}")
        
        elif strategy_type == 'real_llm_embedding':
            if 'embedding_model' in metadata:
                st.write(f"**Embedding Model**: {metadata['embedding_model']}")
            if 'similar_emails_found' in metadata:
                st.write(f"**Similar Emails**: {metadata['similar_emails_found']}")
        
        elif strategy_type == 'real_llm_outcomes':
            if 'recent_results_used' in metadata:
                st.write(f"**Historical Data**: {metadata['recent_results_used']} recent results")
        
        # Error information
        if 'error' in metadata:
            st.error(f"**Error**: {metadata.get('error_message', 'Unknown error')}")

def display_summary(triage_results):
    """Display a summary of all triage results"""
    if not triage_results:
        st.warning("No triage results to summarize")
        return
    
    # Create a summary table
    summary_data = []
    real_llm_count = 0
    fallback_count = 0
    
    for strategy, result in triage_results.items():
        if result:
            strategy_type = result.get('metadata', {}).get('strategy', 'unknown')
            is_real_llm = 'real_llm' in strategy_type
            
            if is_real_llm:
                real_llm_count += 1
            else:
                fallback_count += 1
            
            summary_data.append({
                'Strategy': strategy.replace('_', ' ').title(),
                'Priority': result.get('priority', 'N/A'),
                'Confidence': f"{result.get('confidence', 0):.1%}",
                'Type': '🤖 Real LLM' if is_real_llm else '⚠️ Fallback',
                'Status': '✅' if result.get('confidence', 0) > 0.5 else '⚠️'
            })
    
    if summary_data:
        st.dataframe(summary_data, use_container_width=True)
    
    # Analysis type summary
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Real LLM Calls", real_llm_count)
    with col2:
        st.metric("Fallback Analyses", fallback_count)
    
    # Consensus analysis
    st.subheader("Consensus Analysis")
    
    priorities = [r.get('priority') for r in triage_results.values() if r and r.get('priority')]
    if priorities:
        most_common = max(set(priorities), key=priorities.count)
        st.info(f"Most common priority across strategies: **{most_common.replace('_', ' ').title()}**")
    
    # Average confidence
    confidences = [r.get('confidence', 0) for r in triage_results.values() if r]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        st.info(f"Average confidence across strategies: **{avg_confidence:.1%}**")

if __name__ == "__main__":
    main() 