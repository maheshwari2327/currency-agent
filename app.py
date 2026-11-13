"""
Currency Agent — Streamlit Web Application
------------------------------------------
Interactive web UI providing:
1. Conversational AI chat with ReAct thought tracing
2. Quick Conversion Calculator with currency swap
3. Real-time ECB reference rate cards
4. Comprehensive 170+ currency directory and guide
"""

import streamlit as st
from currency_service import (
    convert_currency_service,
    CURRENCY_NAMES,
    REFERENCE_RATES_USD,
    REFERENCE_DATE
)
from agent import run_agent, is_ollama_available

# Page configuration
st.set_page_config(
    page_title="Currency Agent — Live ECB Exchange Rates",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #BAE6FD;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0369A1;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 500;
    }
    .result-box {
        background-color: #F8FAFC;
        border-left: 5px solid #2563EB;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin: 0.8rem 0;
    }
    .result-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1E293B;
    }
    .result-sub {
        font-size: 0.95rem;
        color: #64748B;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to the Currency Agent!**\n\n"
                "I convert money across **170+ world currencies** using official daily reference rates "
                "from the European Central Bank. You can talk to me in plain English, for example:\n\n"
                "- *\"Convert 100 USD to EUR\"*\n"
                "- *\"How much is 500 euros in Indian rupees?\"*\n"
                "- *\"What is 1000 dollars in Japanese yen?\"*\n"
                "- *\"Convert 200 pounds to Canadian dollars\"*"
            ),
            "steps": []
        }
    ]

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Agent Settings")
    
    ollama_online = is_ollama_available()
    if ollama_online:
        st.success("🟢 Ollama Engine: Online (`llama3.2`)")
        default_mode = "Live Ollama (`llama3.2`)"
    else:
        st.info("🟡 Ollama Engine: Offline (Local server not detected)")
        default_mode = "Mock / Fast ReAct Mode"

    agent_mode = st.radio(
        "Execution Engine",
        options=["Mock / Fast ReAct Mode", "Live Ollama (`llama3.2`)"],
        index=0 if not ollama_online else 1,
        help="Mock mode demonstrates the full ReAct cycle instantly without needing a local LLM server running."
    )
    use_mock = (agent_mode == "Mock / Fast ReAct Mode")

    st.markdown("---")
    st.subheader("⚡ Quick Converter")

    curr_list = sorted(list(CURRENCY_NAMES.keys()))
    
    calc_amount = st.number_input("Amount", min_value=0.01, value=100.0, step=10.0)
    
    col_from, col_to = st.columns(2)
    with col_from:
        calc_from = st.selectbox("From", curr_list, index=curr_list.index("USD") if "USD" in curr_list else 0)
    with col_to:
        calc_to = st.selectbox("To", curr_list, index=curr_list.index("EUR") if "EUR" in curr_list else 1)

    if st.button("Convert Instantly", use_container_width=True, type="primary"):
        quick_res = convert_currency_service(calc_amount, calc_from, calc_to)
        if quick_res.get("success"):
            st.success(f"**{quick_res['formatted_amount']} {quick_res['from_currency']} = {quick_res['formatted_converted']} {quick_res['to_currency']}**")
            st.caption(f"1 {quick_res['from_currency']} = {quick_res['formatted_rate']} {quick_res['to_currency']} (as of {quick_res['date']})")
        else:
            st.error(quick_res.get("error"))

    st.markdown("---")
    st.markdown("### ℹ️ Good to Know")
    st.markdown("""
    - **Daily Updates:** Sourced directly from European Central Bank official feeds.
    - **Free & Keyless:** No account or API keys required.
    - **170+ Currencies:** Comprehensive global fiat coverage.
    - **No Crypto:** Crypto assets (BTC, ETH, etc.) are excluded per ECB focus.
    """)

# Main Content Header
st.markdown('<div class="main-header">💱 Currency Agent — Plain English Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Converts money between 170+ currencies using official European Central Bank reference rates</div>', unsafe_allow_html=True)

# Top Reference Rate Tickers
ticker_cols = st.columns(4)
tickers = [
    ("USD / EUR", 1.0, "USD", "EUR"),
    ("USD / INR", 1.0, "USD", "INR"),
    ("USD / JPY", 1.0, "USD", "JPY"),
    ("GBP / CAD", 1.0, "GBP", "CAD")
]

for idx, (label, amt, f_curr, t_curr) in enumerate(tickers):
    rate_info = convert_currency_service(amt, f_curr, t_curr)
    with ticker_cols[idx]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{rate_info.get('formatted_rate', '—')} {t_curr}</div>
            <div class="metric-label">as of {rate_info.get('date', REFERENCE_DATE)}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick Suggestion Buttons
st.write("**💡 Quick Plain English Prompts (Click to test):**")
prompt_cols = st.columns(4)

suggested_queries = [
    "Convert 1000 USD to JPY",
    "How much is 500 euros in Indian rupees?",
    "What is 1000 dollars in Japanese yen?",
    "Convert 200 pounds to Canadian dollars"
]

selected_prompt = None
for i, query_text in enumerate(suggested_queries):
    with prompt_cols[i]:
        if st.button(query_text, key=f"btn_prompt_{i}", use_container_width=True):
            selected_prompt = query_text

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("steps"):
            with st.expander("🔍 View ReAct Agent Reasoning Trace"):
                for s in msg["steps"]:
                    st.markdown(f"**Thought:** {s.get('thought')}")
                    st.code(f"Action: {s.get('action')}", language="python")
                    st.markdown(f"**Observation:** {s.get('observation')}")

# Chat input handler
user_query = st.chat_input("Ask a conversion question in plain English...") or selected_prompt

if user_query:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Fetching European Central Bank rates..."):
            agent_output = run_agent(user_query, mock=use_mock)
            final_text = agent_output.get("final_answer", "")
            steps = agent_output.get("steps", [])

            st.markdown(final_text)

            if steps:
                with st.expander("🔍 View ReAct Agent Reasoning Trace", expanded=False):
                    for s in steps:
                        st.markdown(f"**Thought:** {s.get('thought')}")
                        st.code(f"Action: {s.get('action')}", language="python")
                        st.markdown(f"**Observation:** {s.get('observation')}")

            # Append assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "steps": steps
            })

# Reference section
with st.expander("📚 Supported Currencies & Technical Details (170+ Currencies)"):
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("### Top Supported Currencies")
        table_rows = [f"| `{code}` | {name} |" for code, name in list(CURRENCY_NAMES.items())[:12]]
        st.markdown("| Code | Currency Name |\n|---|---|\n" + "\n".join(table_rows))
    with col_b:
        st.markdown("### Agent Architecture")
        st.markdown("""
        - **Model / Framework:** LangChain & LangGraph ReAct Cycle
        - **Source:** European Central Bank official reference feed
        - **Fallback:** Offline daily reference rate cache (as of 2026-11-12)
        - **Limitations:**
          - Daily reference rates (not real-time tick-by-tick)
          - Not intended for live trading / excludes bank spreads
          - Cryptocurrency is not supported
        """)
