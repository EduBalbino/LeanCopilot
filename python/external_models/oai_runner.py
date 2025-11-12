from typing import Any, List, Tuple
import json
import os
import openai
from openai import OpenAI
from .external_parser import *


class OpenAIRunner(Generator, Transformer):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    def __init__(self, **args):
        self.model = args["model"]
        self.num_suggestions = args["num_return_sequences"]
        self.max_output_tokens = args["max_tokens"]
        self.timeout = args["openai_timeout"]
        self.temperature = args.get("temperature")
        self.top_p = args.get("top_p")
        self.reasoning = args.get("reasoning")
        self.name = self.model

    def generate(self, input: str, target_prefix: str = "") -> List[Tuple[str, float]]:
        lean_prompt = pre_process_input(self.name, input + target_prefix)
        user_prompt = self._build_user_prompt(lean_prompt, target_prefix)
        request_kwargs: dict[str, Any] = {
            "input": self._build_messages(user_prompt),
            "response_format": self._response_format(),
            "max_output_tokens": self.max_output_tokens,
            "model": self.model,
            "timeout": self.timeout,
        }
        if self.temperature is not None:
            request_kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            request_kwargs["top_p"] = self.top_p
        if self.reasoning is not None:
            request_kwargs["reasoning"] = self.reasoning
        try:
            response = OpenAIRunner.client.responses.create(
                **request_kwargs,
            )
        except (
            openai.APIError,
            openai.RateLimitError,
            openai.InternalServerError,
            openai.OpenAIError,
            openai.APIStatusError,
            openai.APITimeoutError,
            openai.InternalServerError,
            openai.APIConnectionError,
        ) as e:
            print("Exception: ", repr(e))
            print("Consider reducing the number of parallel processes.")
            return OpenAIRunner.generate(self, input, target_prefix)
        except Exception as e:
            print(f"Failed to run the model for {prompt}!")
            print("Exception: ", repr(e))
            raise e

        suggestions = self._extract_suggestions(response)
        payloads = [json.dumps(suggestion, ensure_ascii=False) for suggestion in suggestions]
        results = [(payload, 1.0) for payload in payloads]
        return choices_dedup(results)

    def _build_messages(self, user_prompt: str) -> list[dict[str, Any]]:
        return [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are Lean Copilot, an expert Lean 4 assistant. "
                        "Always follow the requested JSON schema exactly so tools can parse your reply.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt,
                    }
                ],
            },
        ]

    def _build_user_prompt(self, lean_prompt: str, target_prefix: str) -> str:
        prefix_clause = (
            f"Every tactic MUST start with the prefix `{target_prefix}`."
            if target_prefix
            else "Tactics must be single Lean commands that could finish the proof state."
        )
        return (
            f"{lean_prompt}\n\n"
            f"Return a JSON object that matches the provided schema with exactly {self.num_suggestions} "
            "diverse suggestions. Each suggestion must include:\n"
            "- `tactic`: one Lean tactic line (no explanations or markdown).\n"
            "- `explanation`: a concise natural language rationale for the tactic.\n"
            f"{prefix_clause}\n"
            "Avoid using `aesop` and never reference the theorem name directly."
        )

    def _response_format(self) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "lean_tactic_suggestions",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "minItems": self.num_suggestions,
                            "maxItems": self.num_suggestions,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "tactic": {
                                        "type": "string",
                                        "description": "Single Lean tactic line.",
                                    },
                                    "explanation": {
                                        "type": "string",
                                        "description": "Short rationale for why the tactic should work.",
                                    },
                                },
                                "required": ["tactic", "explanation"],
                            },
                        }
                    },
                    "required": ["suggestions"],
                },
            },
        }

    def _extract_suggestions(self, response) -> list[dict[str, str]]:
        text_chunks: list[str] = []
        for item in response.output:
            if item.type != "message":
                continue
            for content in item.content:
                if content.type == "output_text":
                    text_chunks.append(content.text)
        if not text_chunks:
            raise RuntimeError("No textual content returned in response output.")
        raw_text = "".join(text_chunks).strip()
        data = json.loads(raw_text)
        suggestions = data.get("suggestions", [])
        parsed = []
        for suggestion in suggestions[: self.num_suggestions]:
            tactic = suggestion.get("tactic", "").strip()
            explanation = suggestion.get("explanation", "").strip()
            if not tactic:
                continue
            parsed.append({"tactic": tactic, "explanation": explanation})
        if not parsed:
            raise RuntimeError(f"Unable to parse suggestions from payload: {raw_text}")
        return parsed

if __name__ == "__main__":
    generation_kwargs = {
        "model": "gpt-5-mini",
        "temperature": None,
        "max_tokens": 1024,
        "top_p": None,
        "frequency_penalty": None,
        "presence_penalty": None,
        "num_return_sequences": 5,
        "openai_timeout": 45,
        # "stop": args.stop,  # stop is only used for base models currently
    }

    model = OpenAIRunner(**generation_kwargs)
    print(model.generate("n : ℕ\n⊢ gcd n n = n"))
