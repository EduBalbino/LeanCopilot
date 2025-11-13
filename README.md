Lean Copilot: LLMs as Copilots for Theorem Proving in Lean
==========================================================

Lean Copilot allows large language models (LLMs) to be used natively in Lean for proof automation, e.g., suggesting tactics and searching for proofs. This release focuses exclusively on a single external generator powered by **GPT-5-nano**. All requests go through the provided Python server and every proof search issues **at most five completions** per call.

<https://github.com/lean-dojo/LeanCopilot/assets/114432581/ee0f56f8-849e-4099-9284-d8092cbd22a3>

## Table of Contents

1. [Requirements](#requirements)  
1. [Using Lean Copilot in Your Project](#using-lean-copilot-in-your-project)
   1. [Adding Lean Copilot as a Dependency](#adding-lean-copilot-as-a-dependency)
   1. [Getting Started with Lean Copilot](#getting-started-with-lean-copilot)
      1. [Tactic Suggestion](#tactic-suggestion)
      1. [Proof Search](#proof-search)
1. [Advanced Usage](#advanced-usage)
   1. [Tactic APIs](#tactic-apis)
   1. [Configuring the GPT-5-nano Server](#configuring-the-gpt-5-nano-server)
1. [Caveats](#caveats)
1. [Getting in Touch](#getting-in-touch)
1. [Acknowledgements](#acknowledgements)
1. [Citation](#citation)

## Requirements

* Supported platforms: Linux, macOS, Windows and [Windows WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
* Python 3.10+ with `fastapi`, `uvicorn`, `loguru`, and `openai`. (See `python/README.md`.)
* An `OPENAI_API_KEY` that can access `gpt-5-nano`.

## Using Lean Copilot in Your Project

:warning: Your project must use a Lean version of at least `lean4:v4.3.0-rc2`.

### Adding Lean Copilot as a Dependency

1. Add the following line to lakefile.lean, including the quotation marks:

```lean
require LeanCopilot from git "https://github.com/lean-dojo/LeanCopilot.git" @ "LEAN_COPILOT_VERSION"
```

For stable Lean versions (e.g., `v4.24.0`), set `LEAN_COPILOT_VERSION` to be that version. For the latest unstable Lean versions (e.g., `v4.25.0-rc1`), set `LEAN_COPILOT_VERSION` to `main`. In either case, make sure the version is compatible with other dependencies such as mathlib. If your project uses lakefile.toml instead of lakefile.lean, it should include:

```toml
[[require]]
name = "LeanCopilot"
git = "https://github.com/lean-dojo/LeanCopilot.git"
rev = "LEAN_COPILOT_VERSION"
```

2. Run `lake update LeanCopilot`.

3. Run `lake build`.

4. Start the Python server in `python/server.py` (see [Configuring the GPT-5-nano Server](#configuring-the-gpt-5-nano-server)) and ensure it has access to your `OPENAI_API_KEY`.

[Here](https://github.com/yangky11/lean4-example/blob/LeanCopilot-demo) is an example of a Lean package depending on Lean Copilot. If you have problems building the project, our [Dockerfile](./Dockerfile), [build.sh](scripts/build.sh) or [build_example.sh](scripts/build_example.sh) may be helpful.

### Getting Started with Lean Copilot

#### Tactic Suggestion

After `import LeanCopilot`, you can use the tactic `suggest_tactics` to generate tactic suggestions. You can click on any of the suggested tactics to use it in the proof.

<img width="977" alt="suggest_tactics" src="https://github.com/lean-dojo/LeanCopilot/assets/114432581/f06865b6-58be-4938-a75c-2a23484384b4">

You can provide a prefix (e.g., `simp`) to constrain the generated tactics:

<img width="915" alt="suggest_tactics_simp" src="https://github.com/lean-dojo/LeanCopilot/assets/114432581/95dcae31-41cb-451c-9fdf-d73522addb6e">

#### Proof Search

The tactic `search_proof` combines LLM-generated tactics with [aesop](https://github.com/leanprover-community/aesop) to search for multi-tactic proofs. When a proof is found, you can click on it to insert it into the editor.

<img width="824" alt="search_proof" src="https://github.com/lean-dojo/LeanCopilot/assets/114432581/26381fca-da4e-43d9-84b5-7e27b0612626">

#### Running LLMs

LLM inference now goes through the bundled GPT-5-nano gateway. Use the scripts in [`python/`](./python) to point Lean Copilot at a different GPT-5-nano deployment if needed.

<img width="1123" alt="run_llms" src="https://github.com/lean-dojo/LeanCopilot/assets/5431913/a4e5b84b-a797-4216-a416-2958448aeb07">

## Advanced Usage

**This section is only for advanced users who would like to change the default behavior of `suggest_tactics` or `search_proof`, e.g., to point them at a different GPT-5-nano endpoint.**

### Tactic APIs

* Examples in [TacticSuggestion.lean](LeanCopilotTests/TacticSuggestion.lean) showcase how to configure `suggest_tactics`, e.g., to switch between GPT-5-nano servers.
* Examples in [ProofSearch.lean](LeanCopilotTests/ProofSearch.lean) showcase how to configure `search_proof` using options provided by [aesop](https://github.com/leanprover-community/aesop).

### Configuring the GPT-5-nano Server

**Examples in [ModelAPIs.lean](LeanCopilotTests/ModelAPIs.lean) showcase how to register additional GPT-5-nano endpoints or override the default host/port.**

Lean Copilot now treats `Generator` as an alias for [`ExternalGenerator`](LeanCopilot/Models/External.lean) and relies on the `TextToText` interface:

```lean
class TextToText (τ : Type) where
  generate (model : τ) (input : String) (targetPrefix : String) :
    IO $ Array (String × Float)
```

Every request is forwarded to the Python server using the schema described in [external_model_api.yaml](./external_model_api.yaml). Our reference implementation lives in [`python/server.py`](./python/server.py), uses `OpenAIRunner`, and clamps `num_return_sequences` to **exactly five GPT-5-nano completions**.

To run the server:

```bash
cd python
uvicorn server:app --port 23337
```

Make sure `OPENAI_API_KEY` is exported in the same shell. Adjust the host/port in Lean via `registerGenerator` if you proxy the server elsewhere.

### Testing & Monitoring the Server

Our primary verification plan is to exercise the tactic suggestions in `LeanCopilotTests/TacticSuggestion.lean`.

1. Start the Python server (or your systemd unit) so that the `/generate` endpoint is reachable.
2. Run `lake build LeanCopilotTests` (or at least compile `LeanCopilotTests/TacticSuggestion.lean`). The Lean code will surface any API errors immediately.
3. The Python server now enforces OpenAI Structured Outputs—any schema violation or refusal becomes an HTTP error. When that happens, inspect the server logs (e.g., `journalctl -u <your-service-name>`) to diagnose the failure.

This tactic-focused test plan is sufficient for validating changes to the GPT-5-nano server.

## Caveats

* The Python server enforces **exactly five** completions per request to GPT-5-nano. Increase the budget by scaling out servers rather than changing `num_return_sequences`.
* In some cases, `search_proof` produces an erroneous proof with error messages like `fail to show termination for ...`. A temporary workaround is changing the theorem's name before applying `search_proof`. You can change it back after `search_proof` completes.

## Getting in Touch

* For general questions and discussions, please use [GitHub Discussions](https://github.com/lean-dojo/LeanCopilot/discussions).  
* To report a potential bug, please open an issue. In the issue, please include your OS information, the exact steps to reproduce the error on **the latest stable version of Lean Copilot**, and complete logs preferrably in debug mode. **Important: If your issue cannot be reproduced easily, it will be unlikely to receive help.**
* Feature requests and contributions are extremely welcome. Please feel free to start a [discussion](https://github.com/lean-dojo/LeanCopilot/discussions) or open a [pull request](https://github.com/lean-dojo/LeanCopilot/pulls).

## Acknowledgements

* We thank Scott Morrison for suggestions on simplifying Lean Copilot's installation and Mac Malone for helping implement it. Both Scott and Mac work for the [Lean FRO](https://lean-fro.org/).
* We thank Jannis Limperg for supporting our LLM-generated tactics in Aesop (<https://github.com/leanprover-community/aesop/pull/70>).

## Citation

If you find our work useful, please consider citing [our paper](https://arxiv.org/abs/2404.12534):

```BibTeX
@article{song2024lean,
  title={Lean copilot: Large language models as copilots for theorem proving in lean},
  author={Song, Peiyang and Yang, Kaiyu and Anandkumar, Anima},
  journal={arXiv preprint arXiv:2404.12534},
  year={2024}
}
```
