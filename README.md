Lean Copilot: LLMs as Copilots for Theorem Proving in Lean
==========================================================

Lean Copilot allows large language models (LLMs) to be used natively in Lean for proof automation, e.g., suggesting tactics/premises and searching for proofs. You can use our built-in models from [LeanDojo](https://leandojo.org/) or bring your own models that run either locally (w/ or w/o GPUs) or on the cloud.

<https://github.com/lean-dojo/LeanCopilot/assets/114432581/ee0f56f8-849e-4099-9284-d8092cbd22a3>

## Table of Contents

1. [Requirements](#requirements)  
1. [Using Lean Copilot in Your Project](#using-lean-copilot-in-your-project)
   1. [Adding Lean Copilot as a Dependency](#adding-lean-copilot-as-a-dependency)
   1. [Getting Started with Lean Copilot](#getting-started-with-lean-copilot)
      1. [Tactic Suggestion](#tactic-suggestion)
      1. [Proof Search](#proof-search)
      1. [Premise Selection](#premise-selection)
1. [Advanced Usage](#advanced-usage)
   1. [Tactic APIs](#tactic-apis)
   1. [Model APIs](#model-apis)
   1. [Bring Your Own Model](#bring-your-own-model)
1. [Caveats](#caveats)
1. [Getting in Touch](#getting-in-touch)
1. [Acknowledgements](#acknowledgements)
1. [Citation](#citation)

## Requirements

* Supported platforms: Linux, macOS, Windows and [Windows WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
* [Git LFS](https://git-lfs.com/).
* Optional (recommended if you have a [CUDA-enabled GPU](https://developer.nvidia.com/cuda-gpus)): CUDA and [cuDNN](https://developer.nvidia.com/cudnn).
* Required for building Lean Copilot itself (rather than a downstream package): CMake >= 3.7 and a C++17 compatible compiler.

## Using Lean Copilot in Your Project

:warning: Your project must use a Lean version of at least `lean4:v4.3.0-rc2`.

### Adding Lean Copilot as a Dependency

1. Add the package configuration option `moreLinkArgs := #["-L./.lake/packages/LeanCopilot/.lake/build/lib", "-lctranslate2"]` to lakefile.lean. For example,

```lean
package «my-package» {
  moreLinkArgs := #[
    "-L./.lake/packages/LeanCopilot/.lake/build/lib",
    "-lctranslate2"
  ]
}
```

Alternatively, if your project uses lakefile.toml, it should include:

```toml
moreLinkArgs = ["-L./.lake/packages/LeanCopilot/.lake/build/lib", "-lctranslate2"]
```

2. Add the following line to lakefile.lean, including the quotation marks:

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

3. If you are using native Windows, add `<path_to_your_project>/.lake/packages/LeanCopilot/.lake/build/lib` to your `Path` variable in Advanced System Settings > Environment Variables... > System variables. 

4. Run `lake update LeanCopilot`.

5. Run `lake exe LeanCopilot/download` to download the built-in models from Hugging Face to `~/.cache/lean_copilot/`. *Alternatively*, you can download the models from Hugging Face manually from

* [ct2-leandojo-lean4-tacgen-byt5-small](https://huggingface.co/kaiyuy/ct2-leandojo-lean4-tacgen-byt5-small)
* [ct2-leandojo-lean4-retriever-byt5-small](https://huggingface.co/kaiyuy/ct2-leandojo-lean4-retriever-byt5-small)
* [premise-embeddings-leandojo-lean4-retriever-byt5-small](https://huggingface.co/kaiyuy/premise-embeddings-leandojo-lean4-retriever-byt5-small)
* [ct2-byt5-small](https://huggingface.co/kaiyuy/ct2-byt5-small)

6. Run `lake build`.

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

You can also run the inference of any LLMs in Lean, which can be used to build customized proof automation or other LLM-based applications (not limited to theorem proving). It's possible to run arbitrary models either locally or remotely (see [Bring Your Own Model](#bring-your-own-model)).

<img width="1123" alt="run_llms" src="https://github.com/lean-dojo/LeanCopilot/assets/5431913/a4e5b84b-a797-4216-a416-2958448aeb07">

## Advanced Usage

**This section is only for advanced users who would like to change the default behavior of `suggest_tactics` or `search_proof`, e.g., to use different models or hyperparameters.**

### Tactic APIs

* Examples in [TacticSuggestion.lean](LeanCopilotTests/TacticSuggestion.lean) showcase how to configure `suggest_tactics`, e.g., to use different models or generate different numbers of tactics.
* Examples in [ProofSearch.lean](LeanCopilotTests/ProofSearch.lean) showcase how to configure `search_proof` using options provided by [aesop](https://github.com/leanprover-community/aesop).

### Model APIs

**Examples in [ModelAPIs.lean](LeanCopilotTests/ModelAPIs.lean) showcase how to run the inference of different models and configure their parameters (temperature, beam size, etc.).**

Lean Copilot supports two kinds of models: generators and encoders. Generators must implement the `TextToText` interface:

```lean
class TextToText (τ : Type) where
  generate (model : τ) (input : String) (targetPrefix : String) : IO $ Array (String × Float)
```

* `input` is the input string
* `targetPrefix` is used to constrain the generator's output. `""` means no constraint.
* `generate` should return an array of `String × Float`. Each `String` is an output from the model, and `Float` is the corresponding score.

We provide two types of Generators:

* [`ExternalGenerator`](LeanCopilot/Models/External.lean) is hosted either locally or remotely. See [Bring Your Own Model](#bring-your-own-model) for details.
* [`GenericGenerator`](LeanCopilot/Models/Generic.lean) can be anything that implements the `generate` function in the `TextToText` typeclass.

Encoders must implement `TextToVec`:

```lean
class TextToVec (τ : Type) where
  encode : τ → String → IO FloatArray
```

* `input` is the input string
* `encode` should return a vector embedding produced by the model.

Similar to generators, we have `ExternalEncoder` and `GenericEncoder`.

## Vision: GPT-5 as the Tactic Copilot

LeanCopilot is evolving into a lightweight bridge between Lean’s tactic state and the strongest available GPT-5 endpoints. Instead of juggling heavy native runtimes, we focus on this flow:

- Capture the current Lean goal, serialize it, and send it to GPT-5 via the Responses API.
- Enforce a strict JSON schema so the model returns `n` tactics, each with an explanation. No string hacks, no guessing logprobs.
- Surface those tactics in the infoview with clear “thinking…” and completion messages, explanations inline, and the same click-to-apply UX Lean users rely on.

This approach keeps the Lean package lean (no OpenBLAS/CTranslate2), makes the FastAPI side easy to extend, and ensures GPT-5 does the heavy reasoning. If you need another model, just register an external generator; the structured-output plumbing is already in place.

### Bring Your Own Model

In principle, it is possible to run any model using Lean Copilot through `ExternalGenerator` or `ExternalEncoder` (examples in [ModelAPIs.lean](LeanCopilotTests/ModelAPIs.lean)). To use a model, you need to wrap it properly to expose the APIs in [external_model_api.yaml](./external_model_api.yaml). As an example, we provide a [Python API server](./python) and use it to run a few models.

## Caveats

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
