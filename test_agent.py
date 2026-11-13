"""
Test Suite for Currency Agent
-----------------------------
Tests currency conversion service, alias resolution, ReAct agent cycle,
crypto guardrails, tools, and CLI execution.
"""

import subprocess
import pytest
from currency_service import (
    convert_currency_service,
    resolve_currency_code,
    REFERENCE_DATE
)
from agent import (
    run_agent,
    convert_currency,
    get_exchange_rate,
    list_supported_currencies,
    MockCurrencyAgent
)


def test_resolve_currency_code():
    assert resolve_currency_code("USD") == "USD"
    assert resolve_currency_code("dollars") == "USD"
    assert resolve_currency_code("bucks") == "USD"
    assert resolve_currency_code("euros") == "EUR"
    assert resolve_currency_code("pounds") == "GBP"
    assert resolve_currency_code("quid") == "GBP"
    assert resolve_currency_code("indian rupees") == "INR"
    assert resolve_currency_code("yen") == "JPY"
    assert resolve_currency_code("dirhams") == "AED"
    assert resolve_currency_code("bitcoin") == "CRYPTO"
    assert resolve_currency_code("btc") == "CRYPTO"


def test_convert_usd_to_jpy():
    result = convert_currency_service(1000, "USD", "JPY")
    assert result["success"] is True
    assert result["from_currency"] == "USD"
    assert result["to_currency"] == "JPY"
    assert result["rate"] > 0
    assert "1,000 USD =" in result["response_text"]
    assert "JPY" in result["response_text"]
    assert "Exchange rate: 1 USD =" in result["response_text"]
    assert "as of" in result["response_text"]


def test_convert_euros_to_rupees():
    result = convert_currency_service(500, "euros", "Indian rupees")
    assert result["success"] is True
    assert result["from_currency"] == "EUR"
    assert result["to_currency"] == "INR"
    assert result["converted_amount"] > 0
    assert "500 EUR =" in result["response_text"]
    assert "INR" in result["response_text"]


def test_convert_pounds_to_cad():
    result = convert_currency_service(200, "pounds", "Canadian dollars")
    assert result["success"] is True
    assert result["from_currency"] == "GBP"
    assert result["to_currency"] == "CAD"
    assert "200 GBP =" in result["response_text"]


def test_crypto_limitations():
    result = convert_currency_service(1, "BTC", "USD")
    assert result["success"] is False
    assert result.get("is_crypto") is True
    assert "Cryptocurrency is not supported" in result["error"]

    # Test via Mock agent
    agent_res = run_agent("Convert 1 bitcoin to USD", mock=True)
    assert "Cryptocurrency is not supported" in agent_res["final_answer"]


def test_same_currency_conversion():
    result = convert_currency_service(100, "USD", "USD")
    assert result["success"] is True
    assert result["rate"] == 1.0
    assert result["converted_amount"] == 100.0


def test_negative_amount_error():
    result = convert_currency_service(-50, "USD", "EUR")
    assert result["success"] is False
    assert "negative" in result["error"].lower()


def test_direct_tool_invocations():
    # Test convert_currency tool
    out1 = convert_currency.invoke({"amount": 100, "from_currency": "USD", "to_currency": "EUR"})
    assert "100 USD =" in out1
    assert "EUR" in out1

    # Test get_exchange_rate tool
    out2 = get_exchange_rate.invoke({"from_currency": "USD", "to_currency": "EUR"})
    assert "Exchange rate: 1 USD =" in out2

    # Test list_supported_currencies tool
    out3 = list_supported_currencies.invoke({})
    assert "Supported Currencies" in out3
    assert "170+" in out3


def test_mock_agent_react_cycle():
    agent = MockCurrencyAgent()
    res = agent.run("What is 1000 dollars in Japanese yen?")
    assert res["is_mock"] is True
    assert len(res["steps"]) > 0
    step = res["steps"][0]
    assert "Thought:" in f"Thought: {step['thought']}"
    assert "convert_currency" in step["action"]
    assert "Observation" in f"Observation: {step['observation']}"
    assert "1,000 USD =" in res["final_answer"]
    assert "JPY" in res["final_answer"]


def test_cli_subprocess():
    result = subprocess.run(
        ["python", "main.py", "--mock", "Convert 100 USD to EUR"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "100 USD =" in result.stdout
    assert "EUR" in result.stdout
