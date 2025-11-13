import Lean
import Batteries.Data.HashMap
import LeanCopilot.Models.External
import LeanCopilot.Models.Builtin

set_option autoImplicit false

open Batteries Lean

namespace LeanCopilot


abbrev Generator := ExternalGenerator


structure ModelRegistry where
  generators : Std.HashMap String Generator :=
    Std.HashMap.ofList [(Builtin.generator.name, Builtin.generator)]


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


def getGenerator (name : String) : Lean.CoreM Generator := do
  let mr ← getModelRegistry
  match mr.generators[name]? with
  | some model => return model
  | none => throwError s!"unknown generator: {name}"


def registerGenerator (name : String) (model : Generator) : IO Unit := do
  let mr ← getModelRegistry
  modelRegistryRef.modify fun _ =>
    {mr with generators := mr.generators.insert name model}


end LeanCopilot
