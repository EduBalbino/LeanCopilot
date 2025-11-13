from __future__ import annotations

from typing import List, Tuple, Any, Dict, Optional
import os
import json
from pydantic import BaseModel, ConfigDict, Field
from loguru import logger
from openai import OpenAI

from .external_parser import *


MAX_COMPLETIONS = 5
MAX_ATTEMPTS = 3

SCHEMA_INSTRUCTIONS_TEMPLATE = """
You are a Lean 4 assistant. Think through the goal, then respond ONLY with strict JSON:
{
  "explanation": "<brief natural-language summary>",
  "suggestions": [
    {"tactic": "<single Lean tactic>", "confidence": <number between 0 and 1>},
    ...
  ]
}
Return at most {limit} unique suggestions (best-first). Emit no prose outside the JSON object.
"""


class LeanSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tactic: str
    confidence: float = Field(ge=0.0, le=1.0)


class LeanSuggestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    explanation: str
    suggestions: List[LeanSuggestion]


class OpenAIRunner(Generator, Transformer):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    def __init__(self, **args):
        requested = min(args["num_return_sequences"], MAX_COMPLETIONS)
        max_tokens = max(32769, int(args["max_tokens"]))
        self.client_kwargs: Dict[str, Any] = {
            "model": args["model"],
            "max_output_tokens": max_tokens,
            "timeout": args["openai_timeout"],
            "max_suggestions": requested,
        }
        self.text_format = LeanSuggestionResponse
        self.reasoning_config = {"effort": "medium"}
        self.name = self.client_kwargs["model"]

    def generate(self, input: str, target_prefix: str = "") -> List[Tuple[str, float]]:
        user_prompt = pre_process_input(self.name, input + target_prefix)
        system_prompt = SCHEMA_INSTRUCTIONS_TEMPLATE.replace(
            "{limit}", str(self.client_kwargs["max_suggestions"])
        )
        max_tokens = self.client_kwargs["max_output_tokens"]
        last_error: Optional[Exception] = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = OpenAIRunner.client.responses.parse(
                model=self.client_kwargs["model"],
                instructions=system_prompt,
                input=[{"role": "user", "content": user_prompt}],
                text_format=self.text_format,
                max_output_tokens=max_tokens,
                reasoning=self.reasoning_config,
            )

            if self._is_incomplete_due_to_tokens(response):
                new_tokens = max(128, max_tokens // 2)
                if new_tokens == max_tokens:
                    last_error = RuntimeError(
                        "Model stopped early due to max_output_tokens."
                    )
                    break
                logger.warning(
                    "Structured output incomplete (max tokens). Retrying with {} tokens.",
                    new_tokens,
                )
                max_tokens = new_tokens
                continue

            try:
                parsed = self._parse_choices(response)
                return choices_dedup(parsed)
            except RuntimeError as err:
                last_error = err
                logger.warning(
                    "Structured output attempt {}/{} failed: {}",
                    attempt,
                    MAX_ATTEMPTS,
                    err,
                )

        raise last_error or RuntimeError(
            "Model response did not contain structured tactics."
        )

    def _parse_choices(self, response: Any) -> List[Tuple[str, float]]:
        self._raise_on_refusal(response)
        payload = response.output_parsed
        if payload is None:
            payload = self._fallback_parse(response)

        parsed: List[Tuple[str, float]] = []
        for suggestion in payload.suggestions[: self.client_kwargs["max_suggestions"]]:
            tactic = suggestion.tactic.strip()
            if not tactic:
                continue
            confidence = max(0.0, min(1.0, float(suggestion.confidence)))
            parsed.append((post_process_output(self.name, tactic), confidence))
        if not parsed:
            raise RuntimeError("Model response did not contain any valid tactics.")
        return parsed

    def _raise_on_refusal(self, response: Any) -> None:
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", []):
                if getattr(content, "type", None) == "refusal":
                    detail = getattr(content, "refusal", "No explanation provided.")
                    raise RuntimeError(
                        "Model refused to provide tactics: {}".format(detail.strip())
                    )

    def _fallback_parse(self, response: Any) -> LeanSuggestionResponse:
        raw_blocks: List[str] = []
        summary: List[Dict[str, Any]] = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "message":
                continue
            entry: Dict[str, Any] = {"content_types": [], "text_samples": []}
            for content in getattr(item, "content", []):
                if getattr(content, "type", None) == "refusal":
                    detail = getattr(content, "refusal", "No explanation provided.")
                    raise RuntimeError(
                        "Model refused to provide tactics: {}".format(detail.strip())
                    )
                content_type = getattr(content, "type", None)
                entry["content_types"].append(content_type)
                if content_type == "output_text":
                    text = getattr(content, "text", "")
                    if text:
                        raw_blocks.append(text)
                        entry["text_samples"].append(text[:200])
            summary.append(entry)
        for raw in raw_blocks:
            cleaned = self._strip_code_fences(raw)
            if not cleaned:
                continue
            try:
                data = json.loads(cleaned)
                return LeanSuggestionResponse.model_validate(data)
            except Exception as err:
                logger.warning(
                    "Structured output fallback parse failed: {} -- snippet: {}",
                    err,
                    cleaned[:200],
                )

        text_suggestions: List[str] = []
        for raw in raw_blocks:
            for line in raw.splitlines():
                candidate = line.strip().strip(",")
                if not candidate or candidate.startswith("{") or candidate.startswith("}"):
                    continue
                text_suggestions.append(candidate)
                if len(text_suggestions) >= self.client_kwargs["max_suggestions"]:
                    break
            if text_suggestions:
                break

        if text_suggestions:
            logger.warning(
                "Falling back to text heuristics: {}", text_suggestions[:5]
            )
            return LeanSuggestionResponse(
                explanation="Generated via raw text fallback.",
                suggestions=[
                    LeanSuggestion(tactic=tac, confidence=0.0)
                    for tac in text_suggestions
                ],
            )

        if summary:
            try:
                logger.error(
                    "No structured payload recovered. Output summary: {}", summary
                )
            except Exception:
                logger.error("No structured payload recovered. (summary logging failed)")
        try:
            logger.error(
                "Raw response dump (truncated): {}",
                str(getattr(response, "model_dump", lambda: response)())[:2000],
            )
        except Exception as err:
            logger.error("Failed to dump raw response: {}", err)
        raise RuntimeError("Model response did not contain structured tactics.")

    def _strip_code_fences(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return cleaned[start : end + 1]
        return cleaned

    def _is_incomplete_due_to_tokens(self, response: Any) -> bool:
        reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
        status = getattr(response, "status", None)
        return status == "incomplete" and reason == "max_output_tokens"


if __name__ == "__main__":
    generation_kwargs = {
        "model": "gpt-5-mini",
        "temperature": 0.0,
        "max_tokens": 1024,
        "top_p": 1.0,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "num_return_sequences": MAX_COMPLETIONS,
        "openai_timeout": 45,
    }

    model = OpenAIRunner(**generation_kwargs)
    print(model.generate("n : ℕ\n⊢ gcd n n = n"))
