import os
import openai
from typing import Dict, List

OPENAI_ENV = "OPENAI_API_KEY"

def llm_query(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 128, temperature: float = 0.0) -> Dict:
    key = os.environ.get(OPENAI_ENV)
    if not key:
        raise RuntimeError("OpenAI API key not set in environment variable OPENAI_API_KEY")
    openai.api_key = key
    try:
        if model.startswith("gpt-"):
            # ChatCompletion style
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            text = resp.choices[0].message.content
            return {"text": text, "raw": resp}
        else:
            resp = openai.Completion.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            text = resp.choices[0].text
            return {"text": text, "raw": resp}
    except Exception as e:
        return {"error": str(e)}
