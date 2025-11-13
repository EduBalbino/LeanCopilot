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
### Configure Alternative GPT-5-nano Endpoints
-/

def stagingGenerator : Generator :=
  {Builtin.generator with
    host := "127.0.0.1"
    port := 24444
  }

#eval getModelRegistry
#eval registerGenerator "gpt-5-nano-staging" stagingGenerator
#eval getModelRegistry


set_option LeanCopilot.suggest_tactics.model "gpt-5-nano-staging" in
example (a b c : Nat) : a + b + c = a + c + b := by
  try suggest_tactics
  try sorry


/-
The default generator can also be addressed via the OpenAI-prefixed name.
-/

set_option LeanCopilot.suggest_tactics.model "openai/gpt-5-nano" in
example (a b c : Nat) : a + b + c = a + c + b := by
  try suggest_tactics
  try sorry
