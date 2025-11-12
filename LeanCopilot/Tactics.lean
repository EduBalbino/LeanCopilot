import Lean
import Lean.Data.Json
import LeanCopilot.Options
import LeanCopilot.Frontend
import Aesop.Util.Basic
import Batteries.Data.String.Basic
import Batteries.Data.String.Matcher

open Lean Meta Parser Elab Term Tactic


set_option autoImplicit false


namespace LeanCopilot

/--
Structured payload that can optionally attach a natural language justification to a tactic.
-/
structure StructuredSuggestion where
  tactic : String
  explanation : String
deriving Inhabited, FromJson

private def decodeStructuredSuggestion? (raw : String) : Option (String × Option String) := do
  match Json.parse raw with
  | Except.error _ => none
  | Except.ok json =>
      match fromJson? json with
      | Except.error _ => none
      | Except.ok (info : StructuredSuggestion) =>
          let tactic := info.tactic.trim
          if tactic.isEmpty then
            none
          else
            let explanation := info.explanation.trim
            let explanation? := if explanation.isEmpty then none else some explanation
            some (tactic, explanation?)

/--
Pretty-print a list of goals.
-/
def ppTacticState : List MVarId → MetaM String
  | [] => return "no goals"
  | [g] => return (← Meta.ppGoal g).pretty
  | goals =>
      return (← goals.foldlM (init := "") (fun a b => do return s!"{a}\n\n{(← Meta.ppGoal b).pretty}")).trim


/--
Pretty-print the current tactic state.
-/
def getPpTacticState : TacticM String := do
  let goals ← getUnsolvedGoals
  ppTacticState goals


open SuggestTactics in
/--
Generate a list of tactic suggestions.
-/
def suggestTacticsWithMetadata (targetPrefix : String) :
    TacticM (Array (String × Float × Option String)) := do
  let state ← getPpTacticState
  let nm ← getGeneratorName
  let model ← getGenerator nm
  let suggestions ← generate model state targetPrefix
  let structured := suggestions.map fun (raw, score) =>
    match decodeStructuredSuggestion? raw with
    | some (tac, explanation?) => (tac, score, explanation?)
    | none => (raw, score, none)
  -- A temporary workaround to prevent the tactic from using the current theorem.
  -- TODO: Use a more principled way, e.g., see `Lean4Repl.lean` in `LeanDojo`.
  if let some declName ← getDeclName? then
    let theoremName := match declName.toString with
      | "_example" => ""
      | n => n.splitOn "." |>.getLast!
    let theoremNameMatcher := String.Matcher.ofString theoremName
    if ← isVerbose then
      logInfo s!"State:\n{state}"
      logInfo s!"Theorem name:\n{theoremName}"
    let filteredSuggestions := structured.filterMap fun (t, s, explanation?) =>
      let isAesop := t == "aesop"
      let isSelfReference := ¬ (theoremName == "") ∧ (theoremNameMatcher.find? t |>.isSome)
      if isSelfReference ∨ isAesop then none else some (t, s, explanation?)
    return filteredSuggestions
  else
    let filteredSuggestions := structured.filterMap fun (t, s, explanation?) =>
      let isAesop := t == "aesop"
      if isAesop then none else some (t, s, explanation?)
    return filteredSuggestions

/--
Backward-compatible helper that omits explanation metadata.
-/
def suggestTactics (targetPrefix : String) : TacticM (Array (String × Float)) := do
  return (← suggestTacticsWithMetadata targetPrefix).map fun (t, s, _) => (t, s)


/--
Information of a premise.
-/
structure PremiseInfo where
  name : String
  path : String
  code : String
  score : Float


/--
Annotate a premise with its type, doc string, import module path, and definition code.
-/
private def annotatePremise (pi : PremiseInfo) : MetaM String := do
  let declName := pi.name.toName
  try
    let info ← getConstInfo declName
    let premise_type ← Meta.ppExpr info.type
    let some doc_str ← findDocString? (← getEnv) declName
      | return s!"{pi.name} : {premise_type}\n"
    return s!"{pi.name} : {premise_type}\n```doc\n{doc_str}\n```\n"
  catch _ => return s!"{pi.name} needs to be imported from `{pi.path}`.\n```code\n{pi.code}\n```\n"


def retrieve (_input : String) : TacticM (Array PremiseInfo) := do
  throwError "Premise selection is not supported in this build."


def selectPremises : TacticM (Array PremiseInfo) := do
  retrieve ""


syntax "pp_state" : tactic
syntax "suggest_tactics" : tactic
syntax "suggest_tactics" str : tactic
syntax "select_premises" : tactic


macro_rules
  | `(tactic | suggest_tactics%$tac) => `(tactic | suggest_tactics%$tac "")


elab_rules : tactic
  | `(tactic | pp_state) => do
    let state ← getPpTacticState
    logInfo state

  | `(tactic | suggest_tactics%$tac $pfx:str) => do
    let generatorName ← SuggestTactics.getGeneratorName
    logInfoAt tac m!"Lean Copilot ({generatorName}) is thinking..."
    let (tacticsWithScores, elapsed) ← Aesop.time $ suggestTacticsWithMetadata pfx.getString
    logInfoAt tac
      m!"Lean Copilot finished in {elapsed.printAsMillis} and produced {tacticsWithScores.size} tactics."
    if ← isVerbose then
      logInfo s!"{elapsed.printAsMillis} for generating {tacticsWithScores.size} tactics"
    let tactics := tacticsWithScores.map (fun (t, _, _) => t)
    if ← isVerbose then
      logInfo s!"Tactics: {tactics}"
    let range : String.Range := { start := tac.getRange?.get!.start, stop := pfx.raw.getRange?.get!.stop }
    let ref := Syntax.ofRange range
    let tacticAndExplanation := tacticsWithScores.map fun (t, _, explanation?) => (t, explanation?)
    hint ref tacticAndExplanation (← SuggestTactics.checkTactics)

  | `(tactic | select_premises) => do
    throwError "Premise selection is not supported in this build."


end LeanCopilot
