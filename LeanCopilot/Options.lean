import Lean
import LeanCopilot.Models

set_option autoImplicit false

open Lean

namespace LeanCopilot

section


variable {m : Type → Type} [Monad m] [MonadOptions m] [MonadEnv m] [MonadLift IO m]


register_option LeanCopilot.verbose : Bool := {
  defValue := false
  descr := "Whether to log various debugging information."
}


def isVerbose : m Bool := do
  match LeanCopilot.verbose.get? (← getOptions) with
  | some true => return true
  | _ => return false


namespace SuggestTactics


register_option LeanCopilot.suggest_tactics.check : Bool := {
  defValue := true
  descr := "Whether to run the generated tactics."
}

def checkTactics : CoreM Bool := do
  match LeanCopilot.suggest_tactics.check.get? (← getOptions) with
  | some false => return false
  | _ => return true


register_option LeanCopilot.suggest_tactics.model : String := {
  defValue := Builtin.generator.name
}


def getGeneratorName : m String := do
  match LeanCopilot.suggest_tactics.model.get? (← getOptions) with
  | some n => return n
  | _ => return Builtin.generator.name


end SuggestTactics


end

end LeanCopilot
