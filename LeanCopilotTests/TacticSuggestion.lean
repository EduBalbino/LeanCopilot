import LeanCopilot


/-
## Basic Usage
-/


example (a b c : Nat) : a + b + c = a + c + b := by
  suggest_tactics


-- You may provide a prefix to constrain the generated tactics.
example (a b c : Nat) : a + b + c = a + c + b := by
  suggest_tactics "rw"


/-
## Advanced Usage
-/


open Lean Meta LeanCopilot


set_option LeanCopilot.verbose true in
example (a b c : Nat) : a + b + c = a + c + b := by
  suggest_tactics


set_option LeanCopilot.suggest_tactics.check false in
example (a b c : Nat) : a + b + c = a + c + b := by
  suggest_tactics
  sorry


/-
### Bring Your Own Model

1. Make sure the model is up and running, e.g., by going to ./python and running `uvicorn server:app --port 23337`.
2. Uncomment the code below.
-/


/-
def myModel : ExternalGenerator := {
  name := "wellecks/llmstep-mathlib4-pythia2.8b"
  host := "localhost"
  port := 23337
}


#eval registerGenerator "wellecks/llmstep-mathlib4-pythia2.8b" (.external myModel)


set_option LeanCopilot.suggest_tactics.check false in
set_option LeanCopilot.suggest_tactics.model "wellecks/llmstep-mathlib4-pythia2.8b" in
example (a b c : Nat) : a + b + c = a + c + b := by
  suggest_tactics

-/
