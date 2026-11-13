"""
Currency Agent
--------------
A LangChain & LangGraph ReAct Agent that converts money between different currencies
using official reference rates from the European Central Bank.

Supports:
- Live Ollama execution (`llama3.2`) with tool calling
- Mock / Dry-run execution with step-by-step ReAct tracing (Thought -> Action -> Observation -> Final Answer)
- Plain English understanding for currency names, slang, and ISO codes
"""

import re
from typing import Dict, Any, List, Optional
import requests

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from currency_service import (
    convert_currency_service,
    resolve_currency_code,
    CURRENCY_NAMES,
    REFERENCE_DATE,
    CRYPTO_TERMS,
    get_cached_rate
)


# ==========================================
# 1. LangChain Tools
# ==========================================

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts an amount of money from one currency to another using official daily
    reference rates from the European Central Bank.
    
    Args:
        amount: The numerical amount of money to convert (e.g. 100, 500, 1000).
        from_currency: Source currency name, slang, or code (e.g. "USD", "dollars", "euros", "GBP").
        to_currency: Target currency name, slang, or code (e.g. "JPY", "Indian rupees", "EUR", "yen").
    
    Returns:
        Converted amount, exchange rate used, and the rate date.
    """
    result = convert_currency_service(amount, from_currency, to_currency)
    if not result.get("success"):
        return f"Error: {result.get('error')}"
    return result.get("response_text", "")


@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """
    Fetches the latest official daily exchange rate between two currencies.
    
    Args:
        from_currency: The base currency (e.g., "USD", "EUR").
        to_currency: The target currency (e.g., "INR", "JPY").
    """
    result = convert_currency_service(1.0, from_currency, to_currency)
    if not result.get("success"):
        return f"Error: {result.get('error')}"
    from_code = result["from_currency"]
    to_code = result["to_currency"]
    rate_str = result["formatted_rate"]
    date_str = result["date"]
    return f"Exchange rate: 1 {from_code} = {rate_str} {to_code} (as of {date_str})"


@tool
def list_supported_currencies() -> str:
    """
    Lists common supported currencies and confirms coverage of 170+ world currencies.
    """
    top_examples = [
        f"- {code} ({name})" for code, name in list(CURRENCY_NAMES.items())[:10]
    ]
    examples_str = "\n".join(top_examples)
    return (
        f"Supported Currencies (170+ total world currencies):\n"
        f"{examples_str}\n"
        f"...and over 160 more fiat currencies! (Note: Cryptocurrency is not supported)."
    )


ALL_TOOLS = [convert_currency, get_exchange_rate, list_supported_currencies]


# ==========================================
# 2. System Prompt
# ==========================================

SYSTEM_PROMPT = """You are the Currency Agent, an intelligent and friendly assistant specializing in converting money between different currencies.

Key Rules & Capabilities:
1. Always use the `convert_currency` tool to calculate conversions using official European Central Bank reference rates.
2. You understand plain English requests like:
   - "Convert 100 USD to EUR"
   - "How much is 500 euros in Indian rupees?"
   - "What is 1000 dollars in Japanese yen?"
   - "Convert 200 pounds to Canadian dollars"
3. Output format: Present the converted amount clearly along with the exchange rate and the date of the rate:
   [Amount] [FROM] = [Converted] [TO]
   Exchange rate: 1 [FROM] = [Rate] [TO] (as of [Date])
4. Limitations to respect:
   - Rates update daily from the European Central Bank (not real-time tick-by-tick).
   - Not for trading purposes; bank fees or spreads are not included.
   - Cryptocurrency (Bitcoin, Ethereum, Dogecoin, etc.) is strictly NOT supported. Politely decline crypto requests.
5. If the user asks general questions about supported currencies, use the `list_supported_currencies` tool.
"""


# ==========================================
# 3. Ollama Availability Check
# ==========================================

def is_ollama_available(host: str = "http://localhost:11434") -> bool:
    """Checks whether the local Ollama instance is up and responding."""
    try:
        r = requests.get(f"{host}/api/tags", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def get_ollama_agent(model_name: str = "llama3.2"):
    """Initializes a LangGraph ReAct agent powered by Ollama."""
    from langchain_ollama import ChatOllama
    from langgraph.prebuilt import create_react_agent
    
    llm = ChatOllama(model=model_name, temperature=0.0)
    agent_graph = create_react_agent(llm, tools=ALL_TOOLS, prompt=SYSTEM_PROMPT)
    return agent_graph


# ==========================================
# 4. Mock / Offline ReAct Agent
# ==========================================

class MockCurrencyAgent:
    """
    Deterministic ReAct Agent simulator for dry-runs, testing, and offline usage.
    Executes the classic ReAct cycle:
    1. Thought
    2. Action
    3. Observation
    4. Final Answer
    """

    @staticmethod
    def parse_query(query: str) -> Dict[str, Any]:
        """Extracts intent, amount, and currencies from natural language."""
        q = query.strip()
        lower_q = q.lower()

        # Check crypto request
        for crypto in CRYPTO_TERMS:
            if re.search(r'\b' + re.escape(crypto) + r'\b', lower_q):
                return {
                    "type": "crypto",
                    "crypto": crypto
                }

        # Check list currencies request
        if any(phrase in lower_q for phrase in ["which currencies", "list currencies", "supported currencies", "what currencies"]):
            return {"type": "list_currencies"}

        # Pattern 1: "Convert 100 USD to EUR", "1000 dollars in Japanese yen", "convert 200 pounds to Canadian dollars"
        # Handles: convert? <amount> <curr1> (to|in|into) <curr2>
        p1 = re.search(
            r'(?:convert\s+)?([\d,]+(?:\.\d+)?)\s+([a-zA-Z\s]+?)\s+(?:to|in|into)\s+([a-zA-Z\s]+?)(?:\?|\.|$)',
            lower_q
        )
        if p1:
            try:
                amt_str = p1.group(1).replace(',', '')
                amt = float(amt_str)
                from_c = p1.group(2).strip()
                to_c = p1.group(3).strip()
                return {
                    "type": "convert",
                    "amount": amt,
                    "from_currency": from_c,
                    "to_currency": to_c
                }
            except ValueError:
                pass

        # Pattern 2: "How much is 500 euros in Indian rupees?" or "What is 1000 dollars in Japanese yen?"
        p2 = re.search(
            r'(?:how much is|what is|how many)\s+([\d,]+(?:\.\d+)?)\s+([a-zA-Z\s]+?)\s+(?:in|to|worth in)\s+([a-zA-Z\s]+?)(?:\?|\.|$)',
            lower_q
        )
        if p2:
            try:
                amt_str = p2.group(1).replace(',', '')
                amt = float(amt_str)
                from_c = p2.group(2).strip()
                to_c = p2.group(3).strip()
                return {
                    "type": "convert",
                    "amount": amt,
                    "from_currency": from_c,
                    "to_currency": to_c
                }
            except ValueError:
                pass

        # Pattern 3: "rate from USD to EUR" or "exchange rate of USD to EUR"
        p3 = re.search(
            r'(?:rate|exchange rate)(?:\s+from|\s+of)?\s+([a-zA-Z\s]+?)\s+(?:to|in)\s+([a-zA-Z\s]+?)(?:\?|\.|$)',
            lower_q
        )
        if p3:
            return {
                "type": "rate",
                "from_currency": p3.group(1).strip(),
                "to_currency": p3.group(2).strip()
            }

        # Pattern 4: Simple "<amount> <curr1> <curr2>" e.g. "100 USD EUR"
        p4 = re.search(
            r'([\d,]+(?:\.\d+)?)\s+([a-zA-Z]{3})\s+([a-zA-Z]{3})',
            query
        )
        if p4:
            return {
                "type": "convert",
                "amount": float(p4.group(1).replace(',', '')),
                "from_currency": p4.group(2),
                "to_currency": p4.group(3)
            }

        # Fallback greetings or general questions
        if any(w in lower_q for w in ["hi", "hello", "hey", "help", "who are you"]):
            return {"type": "greeting"}

        return {"type": "unknown", "query": query}

    def run(self, query: str) -> Dict[str, Any]:
        """Executes the query through the ReAct loop simulation."""
        parsed = self.parse_query(query)
        steps = []
        q_type = parsed.get("type")

        if q_type == "crypto":
            thought = f"The user asked about cryptocurrency ('{parsed['crypto']}'). According to our guidelines, cryptocurrency is not supported."
            action = "None (Limitation Check)"
            observation = "Cryptocurrency is excluded per policy."
            final_answer = "Cryptocurrency is not supported. This agent converts fiat currencies using official European Central Bank reference rates."
            steps.append({"thought": thought, "action": action, "observation": observation})
            return {
                "final_answer": final_answer,
                "steps": steps,
                "is_mock": True,
                "details": None
            }

        elif q_type == "list_currencies":
            thought = "User wants to know what currencies are supported. I will invoke `list_supported_currencies`."
            action = "list_supported_currencies()"
            observation = list_supported_currencies.invoke({})
            final_answer = observation
            steps.append({"thought": thought, "action": action, "observation": observation})
            return {
                "final_answer": final_answer,
                "steps": steps,
                "is_mock": True,
                "details": None
            }

        elif q_type == "convert":
            amt = parsed["amount"]
            from_c = parsed["from_currency"]
            to_c = parsed["to_currency"]
            thought = f"The user wants to convert {amt} from {from_c} to {to_c}. I will call the `convert_currency` tool."
            action = f"convert_currency(amount={amt}, from_currency='{from_c}', to_currency='{to_c}')"
            
            conversion_res = convert_currency_service(amt, from_c, to_c)
            if conversion_res.get("success"):
                observation = conversion_res["response_text"]
                final_answer = conversion_res["response_text"]
            else:
                observation = f"Error: {conversion_res.get('error')}"
                final_answer = observation

            steps.append({"thought": thought, "action": action, "observation": observation})
            return {
                "final_answer": final_answer,
                "steps": steps,
                "is_mock": True,
                "details": conversion_res if conversion_res.get("success") else None
            }

        elif q_type == "rate":
            from_c = parsed["from_currency"]
            to_c = parsed["to_currency"]
            thought = f"User is asking for exchange rate from {from_c} to {to_c}. I will call `get_exchange_rate`."
            action = f"get_exchange_rate(from_currency='{from_c}', to_currency='{to_c}')"
            observation = get_exchange_rate.invoke({"from_currency": from_c, "to_currency": to_c})
            final_answer = observation
            steps.append({"thought": thought, "action": action, "observation": observation})
            return {
                "final_answer": final_answer,
                "steps": steps,
                "is_mock": True,
                "details": None
            }

        elif q_type == "greeting":
            final_answer = (
                "Hello! I am the Currency Agent. I can convert money between 170+ currencies "
                "using official European Central Bank reference rates.\n\n"
                "Try asking me:\n"
                "- 'Convert 100 USD to EUR'\n"
                "- 'How much is 500 euros in Indian rupees?'\n"
                "- 'What is 1000 dollars in Japanese yen?'\n"
                "- 'Convert 200 pounds to Canadian dollars'"
            )
            return {
                "final_answer": final_answer,
                "steps": [{"thought": "User gave a greeting.", "action": "Respond with greeting and examples", "observation": "Ready"}],
                "is_mock": True,
                "details": None
            }

        else:
            final_answer = (
                f"I couldn't quite extract the currency conversion from: \"{query}\".\n"
                "Please specify an amount and two currencies, for example:\n"
                "- 'Convert 1000 USD to JPY'\n"
                "- 'How much is 500 EUR in INR?'"
            )
            return {
                "final_answer": final_answer,
                "steps": [{"thought": f"Unable to parse query '{query}'.", "action": "Ask for clarification", "observation": "Guidance provided"}],
                "is_mock": True,
                "details": None
            }


# ==========================================
# 5. Unified Agent Invoker
# ==========================================

def run_agent(query: str, mock: bool = False, model_name: str = "llama3.2") -> Dict[str, Any]:
    """
    Runs the Currency Agent:
    - If mock=True or Ollama is offline: uses deterministic ReAct simulator MockCurrencyAgent.
    - If Ollama is available and mock=False: executes live LangGraph ReAct agent.
    """
    if mock or not is_ollama_available():
        mock_agent = MockCurrencyAgent()
        return mock_agent.run(query)

    # Live Ollama ReAct execution
    try:
        agent_graph = get_ollama_agent(model_name=model_name)
        inputs = {"messages": [HumanMessage(content=query)]}
        response = agent_graph.invoke(inputs)
        messages = response.get("messages", [])
        
        steps = []
        final_answer = ""
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    steps.append({
                        "thought": "Invoking tool based on user query.",
                        "action": f"{tc['name']}({tc['args']})",
                        "observation": "Executed"
                    })
            if msg.type == "ai" and msg.content and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                final_answer = msg.content

        if not final_answer and messages:
            final_answer = messages[-1].content

        return {
            "final_answer": final_answer,
            "steps": steps,
            "is_mock": False,
            "details": None
        }
    except Exception as e:
        # Fallback to mock agent if Ollama execution errors out
        mock_agent = MockCurrencyAgent()
        res = mock_agent.run(query)
        res["note"] = f"Fell back to rule-based ReAct agent due to Ollama error: {str(e)}"
        return res
