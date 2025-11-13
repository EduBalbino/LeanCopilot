import Lean
import Batteries.Data.HashMap
import LeanCopilot.Models.External
import LeanCopilot.Models.Interface
import LeanCopilot.Models.Builtin

set_option autoImplicit false

open Batteries Lean

namespace LeanCopilot


inductive Generator where
  | external : ExternalGenerator → Generator
deriving Repr


instance : Coe ExternalGenerator Generator := ⟨Generator.external⟩


instance : TextToText Generator where
  generate
  | .external model => TextToText.generate model input targetPrefix


structure ModelRegistry where
  generators : Std.HashMap String Generator :=
    Std.HashMap.ofList [(Builtin.generator.name, (Builtin.generator : Generator))]


namespace ModelRegistry


def generatorNames (mr : ModelRegistry) : List String :=
  mr.generators.toList.map (·.1)


end ModelRegistry


instance : Repr ModelRegistry where
  reprPrec mr n := reprPrec mr.generatorNames n


instance : Inhabited ModelRegistry where
  default := {}


initialize modelRegistryRef : IO.Ref ModelRegistry ← IO.mkRef default


def getModelRegistry : IO ModelRegistry :=
  modelRegistryRef.get


private def normalizeGeneratorName (name : String) : List String :=
  let openAiPrefix := "openai/"
  let mut candidates : List String := []
  if name.startsWith openAiPrefix then
    let alias := name.drop openAiPrefix.length
    if alias ≠ "" then
      candidates := alias :: candidates
  candidates


def getGenerator (name : String) : Lean.CoreM Generator := do
  let mr ← getModelRegistry
  match mr.generators[name]? with
  | some model => return model
  | none =>
      for alias in normalizeGeneratorName name do
        if let some model := mr.generators[alias]? then
          return model
      throwError s!"unknown generator: {name}"


def registerGenerator (name : String) (model : Generator) : IO Unit := do
  let mr ← getModelRegistry
  modelRegistryRef.modify fun _ =>
    {mr with generators := mr.generators.insert name model}


end LeanCopilot
