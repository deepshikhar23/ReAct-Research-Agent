# app.py (Version 18 - The Final Stable UI)

import streamlit as st
from agent.agent_core import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="🧠 Intelligent Research Agent", layout="wide")


# --- SESSION STATE INITIALIZATION ---
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- HELPER FUNCTIONS ---
def initialize_agent():
    if st.session_state.agent_executor is None:
        try:
            st.session_state.agent_executor = create_agent(st.secrets["TAVILY_API_KEY"])
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}", icon="🚨")
            st.stop()

def format_thinking_log(intermediate_steps):
    """
    Formats the structured intermediate steps into a readable log.
    """
    if not intermediate_steps:
        return "🧠 **Thought:** The agent answered directly from the conversation history."

    log = "Here is my thought process:\n\n"
    for action, observation in intermediate_steps:
        # action.log contains the structured Thought, Action, and Action Input
        log += action.log
        log += f"\nObservation: A response was received from the tool."
        log += "\n\n---\n\n"
        
    return log


# --- UI RENDERING ---
st.title("🧠 Intelligent Research Agent")

with st.sidebar:
    st.header("About")
    st.markdown("""
    This is an AI research assistant designed to provide well-sourced, up-to-date answers by searching the web. 
    It uses the **ReAct (Reasoning and Acting)** framework to break down complex questions, create a plan, and execute it step-by-step.
    """)
    st.header("Features")
    st.markdown("""
    - **Conversational Memory:** Remembers the context for follow-up questions.
    - **Source Citations:** Provides links to the sources it used.
    - **Persistent Thinking Log:** See the agent's step-by-step reasoning for every answer.
    - **Deep Dive Mode:** Conducts more thorough research when enabled.
    """)
    is_deep_dive = st.checkbox("Enable Deep Dive Mode", value=False)
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

initialize_agent()

# Display chat messages from history
for message in st.session_state.chat_history:
    role = message.get("role")
    content = message.get("content")
    thoughts = message.get("thoughts", "")
    with st.chat_message(role, avatar="🧠" if role == "ai" else "👤"):
        st.markdown(content)
        if thoughts:
            with st.expander("View thought process"):
                st.text(thoughts) 

# Get user input
user_prompt = st.chat_input("Ask me anything...")

if user_prompt:
    st.session_state.chat_history.append({"role": "human", "content": user_prompt})
    with st.chat_message("human", avatar="👤"):
        st.markdown(user_prompt)

    with st.chat_message("ai", avatar="🧠"):
        if st.session_state.agent_executor:
            with st.spinner("Agent is thinking..."):
                if is_deep_dive: user_prompt_full = f"{user_prompt} (Deep Dive Mode is ON)"
                else: user_prompt_full = user_prompt
                
                current_date_str = datetime.now().strftime("%B %d, %Y")
                history_for_agent = [AIMessage(content=msg["content"]) if msg["role"] == "ai" else HumanMessage(content=msg["content"]) for msg in st.session_state.chat_history]

                response = st.session_state.agent_executor.invoke({
                    "input": user_prompt_full,
                    "chat_history": history_for_agent,
                    "current_date": current_date_str
                })
                
                final_response = response.get("output", "I could not find an answer.")
                intermediate_steps = response.get("intermediate_steps", [])
                thinking_log = format_thinking_log(intermediate_steps)
            
            st.markdown(final_response)
            if thinking_log:
                with st.expander("View thought process"):
                    st.text(thinking_log)
            
            st.session_state.chat_history.append({"role": "ai", "content": final_response, "thoughts": thinking_log})
        else:
            st.error("Agent not initialized! Please ensure your API keys are correctly set in secrets.toml.", icon="🚨")