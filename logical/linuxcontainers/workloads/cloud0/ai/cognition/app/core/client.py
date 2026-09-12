from openai import OpenAI
from ..config import vLLM_URL

# Global instance of the OpenAI client for the vLLM server
openai_client = OpenAI(base_url=vLLM_URL, api_key="empty")
