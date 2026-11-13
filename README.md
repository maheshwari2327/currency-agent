# Currency Agent — Plain English Guide

## What does this agent do?

This agent converts money between different currencies using live exchange rates. Ask it how much your money is worth in another country's currency and it will tell you instantly.

## How to talk to it

Just ask in plain English:

- "Convert 100 USD to EUR"
- "How much is 500 euros in Indian rupees?"
- "What is 1000 dollars in Japanese yen?"
- "Convert 200 pounds to Canadian dollars"

## How it works (simple version)

1. You tell it the amount and the two currencies
2. It fetches the latest exchange rate (updated daily from the European Central Bank)
3. It calculates the converted amount
4. It shows you the result with the rate used

## What you get back

- The converted amount
- The exchange rate (e.g., 1 USD = 83.50 INR)
- The date the rate is from

## Supported currencies (examples)

| Code | Currency |
|------|----------|
| USD | US Dollar |
| EUR | Euro |
| GBP | British Pound |
| INR | Indian Rupee |
| JPY | Japanese Yen |
| AUD | Australian Dollar |
| CAD | Canadian Dollar |
| AED | UAE Dirham |

170+ currencies total — just ask!

## Example conversation

> **You:** Convert 1000 USD to JPY
>
> **Agent:** 1,000 USD = 149,250 JPY
> Exchange rate: 1 USD = 149.25 JPY (as of 2026-11-12)

## Good to know

- Rates update **daily** (not real-time tick-by-tick)
- Completely free, no account or API key needed
- Uses European Central Bank official reference rates
- You can say "dollars", "euros", "rupees" and it will understand

## Limitations

- Not for trading — rates are daily reference rates, not live market prices
- Does not include bank fees or spreads (actual exchange at a bank may differ)
- Cryptocurrency is not supported

---

# Technical Documentation & Usage Guide

### Architecture Overview

The **Currency Agent** is built using **LangChain** and **LangGraph** following the **ReAct (Reasoning + Acting)** framework:

```
User Query ("Convert 1000 USD to JPY")
                │
                ▼
      [ LangGraph ReAct Agent ]
                │
                ├─ Thought: User needs conversion from USD to JPY
                ├─ Action: convert_currency(amount=1000, from='USD', to='JPY')
                │       │
                │       ▼
                │ [ Currency Service ]
                │   ├── 1. Live Frankfurter API (ECB reference rates)
                │   ├── 2. Open Exchange Rates API (170+ currencies)
                │   └── 3. Embedded ECB Reference Rate Archive (Offline fallback)
                │
                ├─ Observation: 1,000 USD = 149,250 JPY (Rate: 149.25 as of 2026-11-12)
                │
                ▼
       Final Agent Response
```

### Project Structure

```
currency agent/
├── README.md               # Plain English guide & technical docs
├── agent.py                # LangChain & LangGraph ReAct agent & tools
├── currency_service.py     # Live ECB rate fetcher, alias resolution & cache
├── main.py                 # CLI interface (Interactive & Single Query)
├── app.py                  # Streamlit web application
├── test_agent.py           # Pytest test suite (100% pass)
└── requirements.txt        # Python dependencies
```

---

### How to Run

#### 1. Requirements Installation
```bash
pip install -r requirements.txt
```

#### 2. Interactive CLI Mode
Start the interactive conversation loop in your terminal:
```bash
python main.py
```

#### 3. Single Query via CLI
Pass a single prompt directly as an argument:
```bash
python main.py "Convert 1000 USD to JPY"
python main.py "How much is 500 euros in Indian rupees?"
```

#### 4. Mock / Offline Mode
Run the agent in mock mode to observe the deterministic ReAct cycle without requiring a running Ollama server:
```bash
python main.py --mock "Convert 200 pounds to Canadian dollars"
```

#### 5. Streamlit Web App
Launch the rich visual web interface:
```bash
streamlit run app.py
```

Features included in the web app:
- Conversational chat interface with reasoning trace expanders
- Quick Conversion Calculator with instant currency swapping
- Live ECB exchange rate ticker cards
- 1-click test prompt suggestions

---

### Running the Test Suite
Run the automated pytest test suite:
```bash
pytest test_agent.py -v
```
All 10 unit and integration tests verify:
- Currency conversion math and output formatting
- Natural language currency name and slang mapping
- Cryptocurrency guardrail enforcement
- ReAct step generation (Thought, Action, Observation)
- Direct tool invocation
- CLI subprocess execution
