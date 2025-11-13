import torch
import numpy as np
from typing import List, Tuple
from abc import ABC, abstractmethod


def get_cuda_if_available():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def pre_process_input(model_name, state: str, target_prefix: str = ""):
    state_block = state.strip()
    prefix_hint = (
        f"\nOnly return tactics that start with `{target_prefix}`."
        if target_prefix
        else ""
    )

    if model_name in [
        "internlm/internlm2-math-plus-1_8b",
        "AI-MO/Kimina-Prover-Preview-Distill-7B",
    ]:
        prompt = (
            "My LEAN 4 state is:\n```lean\n"
            + state_block
            + "\n```\nPlease predict a possible tactic to help me prove the theorem."
            + prefix_hint
        )
        prompt = f"""<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"""
    elif (
        model_name in ["gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-5-nano"]
        or "gemini" in model_name
        or "claude" in model_name
    ):
        prompt = (
            "You are given the current Lean 4 goal and context:\n```lean\n"
            + state_block
            + "\n```\nSuggest a single Lean tactic that can make progress."
            + prefix_hint
            + "\nRespond with the tactic only (no leading `by`)."
        )
    else:
        raise NotImplementedError(f"External model '{model_name}' not supported")
    return prompt


def post_process_output(model_name, output):
    if model_name == "internlm/internlm2-math-plus-1_8b":
        result = (
            output.split("assistant")[-1]
            .split("lean")[-1]
            .split("```")[0]
            .split("\n")[1]
        )
    elif model_name == "AI-MO/Kimina-Prover-Preview-Distill-7B":
        result = (
            output.split("assistant")[-1]
            .split("lean")[-1]
            .split("```")[0]
            .split("\n")[-2]
            .lstrip()
        )
    elif model_name in ["gpt-3.5-turbo", "gpt-4-turbo-preview"]:
        result = output.split("lean")[-1].split("```")[0].split("\n")[1]
    elif model_name == "gpt-5-nano":
        result = output.strip()
        if result.startswith("by") and (len(result) == 2 or result[2].isspace()):
            result = result[2:].lstrip()
    elif "gemini" in model_name or "claude" in model_name:
        result = output.split("lean")[-1].split("```")[0].split("\n")[1]
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
