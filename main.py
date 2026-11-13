"""
Currency Agent CLI
------------------
Interactive CLI and single-query runner for the Currency Agent.

Usage:
    # Interactive CLI:
    python main.py

    # Single query (Live Ollama if available):
    python main.py "Convert 1000 USD to JPY"

    # Mock / dry-run mode (demonstrates ReAct cycle without Ollama):
    python main.py --mock "Convert 500 euros to Indian rupees"

    # Verbose mode (shows Thought -> Action -> Observation steps):
    python main.py --verbose "What is 1000 dollars in Japanese yen?"
"""

import sys
import argparse
from agent import run_agent, is_ollama_available

BANNER = r"""
===================================================================
                  Currency Agent (ECB Reference)
===================================================================
Converts money using official European Central Bank reference rates.
Supports 170+ world currencies. Ask in plain English!

Example questions:
  * "Convert 100 USD to EUR"
  * "How much is 500 euros in Indian rupees?"
  * "What is 1000 dollars in Japanese yen?"
  * "Convert 200 pounds to Canadian dollars"
Type 'exit' or 'quit' to leave.
===================================================================
"""


def print_steps(steps: list):
    """Prints the internal ReAct reasoning cycle."""
    if not steps:
        return
    print("\n--- [ReAct Reasoning Cycle] ---")
    for idx, s in enumerate(steps, 1):
        if s.get("thought"):
            print(f"  [Step {idx}] Thought: {s['thought']}")
        if s.get("action"):
            print(f"          Action:  {s['action']}")
        if s.get("observation"):
            print(f"          Observe: {s['observation']}")
    print("-------------------------------\n")


def interactive_mode(mock: bool = False, verbose: bool = False, model: str = "llama3.2"):
    """Runs the interactive conversation loop."""
    print(BANNER)
    
    ollama_up = is_ollama_available()
    active_mock = mock or (not ollama_up)
    
    status_label = "MOCK / OFFLINE MODE" if active_mock else f"LIVE OLLAMA ({model})"
    print(f"Engine Status: {status_label}")
    if not ollama_up and not mock:
        print("Notice: Ollama service is not running locally. Running in Mock/Dry-Run ReAct mode.")
    print("")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break

            if user_input.lower() == "help":
                print("\nPlain English examples:")
                print(" - Convert 1000 USD to JPY")
                print(" - How much is 500 euros in Indian rupees?")
                print(" - What is 1000 dollars in Japanese yen?")
                print(" - Convert 200 pounds to Canadian dollars")
                print(" - List supported currencies\n")
                continue

            if user_input.lower() == "toggle mock":
                active_mock = not active_mock
                mode_str = "MOCK" if active_mock else "LIVE OLLAMA"
                print(f"Switched mode to: {mode_str}\n")
                continue

            res = run_agent(user_input, mock=active_mock, model_name=model)
            
            if verbose or active_mock:
                print_steps(res.get("steps", []))
                
            print(f"Agent:\n{res['final_answer']}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Currency Agent — Converts currencies using European Central Bank reference rates"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Single query to execute (e.g. 'Convert 1000 USD to JPY')"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock/offline mode (demonstrates ReAct cycle without Ollama)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose ReAct reasoning steps (Thought -> Action -> Observation)"
    )
    parser.add_argument(
        "--model",
        default="llama3.2",
        help="Ollama model to use for live execution (default: llama3.2)"
    )

    args = parser.parse_args()

    if args.query:
        # Single query mode
        res = run_agent(args.query, mock=args.mock, model_name=args.model)
        if args.verbose or args.mock:
            print_steps(res.get("steps", []))
        print(res["final_answer"])
    else:
        # Interactive CLI mode
        interactive_mode(mock=args.mock, verbose=args.verbose, model=args.model)


if __name__ == "__main__":
    main()
