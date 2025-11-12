import torch
import numpy as np
import re
from typing import List, Tuple
from abc import ABC, abstractmethod


def get_cuda_if_available():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def pre_process_input(model_name, input):
    if model_name == "internlm/internlm2-math-plus-1_8b" or model_name == "AI-MO/Kimina-Prover-Preview-Distill-7B":    
        prompt = (
            "My LEAN 4 state is:\n```lean\n"
            + input
            + "```\nPlease predict a possible tactic to help me prove the theorem."
        )
        prompt = f"""<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"""
    elif model_name in {
        "gpt-5-mini",
        "gpt-5-nano",
    }:
        prompt = (
            "Here is a theorem you need to prove in Lean:\n"
            + input
            + "\nNow you should suggest one line tactic in lean code:"
        )
    elif "gemini" in model_name or "claude" in model_name:
        prompt = (
            "Here is a theorem you need to prove in Lean:\n"
            + input
            + "\nNow you should suggest one line tactic in lean code:"
        )
    else:
        raise NotImplementedError(f"External model '{model_name}' not supported")
    return prompt


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _extract_tactic(candidate: str) -> str:
    matches = re.findall(r'"([^"]+)"', candidate)
    if matches:
        return matches[0].strip()
    return candidate.strip()


def post_process_output(model_name, output):
    if model_name == "internlm/internlm2-math-plus-1_8b":
        result = (
            output.split("assistant")[-1]
            .split("lean")[-1]
            .split("```")[0]
        )
        result = _first_non_empty_line(result)
    elif model_name == "AI-MO/Kimina-Prover-Preview-Distill-7B":
        result = (
            output.split("assistant")[-1]
            .split("lean")[-1]
            .split("```")[0]
        )
        lines = [line.strip() for line in result.splitlines() if line.strip()]
        result = lines[-1] if lines else ""
    elif model_name in {
        "gpt-5-mini",
        "gpt-5-nano",
    }:
        chunk = output.split("lean")[-1].split("```")[0]
        result = _extract_tactic(_first_non_empty_line(chunk))
    elif "gemini" in model_name or "claude" in model_name:
        chunk = output.split("lean")[-1].split("```")[0]
        result = _extract_tactic(_first_non_empty_line(chunk))
    else:
        raise NotImplementedError(f"External model '{model_name}' not supported")
    return result


def choices_dedup(output_list: List[tuple[str, float]]) -> List[tuple[str, float]]:
    unique_data = {}
    for item in output_list:
        if item[0] not in unique_data or item[1] > unique_data[item[0]]:
            unique_data[item[0]] = item[1]
    sorted_data = sorted(unique_data.items(), key=lambda x: x[1], reverse=True)
    return sorted_data


class Generator(ABC):
    @abstractmethod
    def generate(self, input: str, target_prefix: str = "") -> List[Tuple[str, float]]:
        pass


class Encoder(ABC):
    @abstractmethod
    def encode(self, input: str) -> np.ndarray:
        pass


class Transformer:
    def cuda(self) -> None:
        self.model.cuda()

    def cpu(self) -> None:
        self.model.cpu()

    @property
    def device(self) -> torch.device:
        return self.model.device
