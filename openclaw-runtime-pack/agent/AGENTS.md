Decision tree:
1. If user input is long, summarize intent before planning.
2. If tool output is large, hand it to a sub-agent and keep only the summary.
3. If knowledge is long, keep only a vault pointer or a short excerpt.
4. If the session grows, compact history before the next model call.
5. Reply briefly and keep the orchestrator context lean.
