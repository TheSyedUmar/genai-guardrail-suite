"""All settings in one place. Values come from the .env file or environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

# Groq gives a free, OpenAI-compatible API, so we use the official `openai` library
# and just point it at Groq's URL.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Check the current model list at https://console.groq.com/docs/models
CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-oss-20b")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")

# A fake "confidential" value planted in the system prompt. The security tests
# try to trick the bot into leaking it.
SECRET_CODE = os.getenv("SECRET_CODE", "ZEBRA-4471")

# Turn the output guardrail on/off to demo the test suite catching leaks.
ENABLE_OUTPUT_GUARD = os.getenv("ENABLE_OUTPUT_GUARD", "true").lower() == "true"
