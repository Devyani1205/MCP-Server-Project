import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqProvider:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception:
                # Keep startup resilient for MCP stdio handshake.
                pass

    def get_recommendation(self, query: str, matched_tests: list) -> dict:
        model = "llama-3.3-70b-versatile"

        prompt = f"""
Doctor query: {query}

Available tests:
{json.dumps(matched_tests, indent=2)}

Suggest the best test and provide a short professional reason.
Return JSON only:
{{
  "recommended_test": "...",
  "reason": "..."
}}
"""

        try:
            if not self.client:
                return {
                    "recommended_test": None,
                    "reason": "AI service unavailable: GROQ_API_KEY missing or invalid."
                }

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=model,
                response_format={"type": "json_object"}
            )

            raw_response = chat_completion.choices[0].message.content
            return json.loads(raw_response)

        except Exception as e:
            return {
                "recommended_test": None,
                "reason": f"AI service unavailable: {str(e)}"
            }


groq_provider = GroqProvider()