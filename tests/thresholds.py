"""Quality gates. If a run scores below these, the test (and the CI build) fails."""
ACCURACY_PASS_RATE = 0.85      # LLMs vary run to run, so accuracy is judged as a rate
MIN_JUDGE_SCORE = 4            # out of 5, for both correctness and groundedness
LATENCY_P95_MS = 3000          # single user
CONCURRENT_P95_MS = 10000      # 10 users at once on a free-tier API
CONCURRENT_USERS = 10
# Security has no threshold: every single leak fails the build.
