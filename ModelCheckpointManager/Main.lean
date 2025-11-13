import ModelCheckpointManager.Url
import ModelCheckpointManager.Download

open LeanCopilot


def builtinModelUrls : List String := []


def main (args : List String) : IO Unit := do
  let mut tasks := #[]
  let urls := Url.parse! <$> (if args.isEmpty then builtinModelUrls else args)

  for url in urls do
    tasks := tasks.push $ ← IO.asTask $ downloadUnlessUpToDate url

  for t in tasks do
    match ← IO.wait t with
    | Except.error e => throw e
    | Except.ok _ => pure ()

  if urls.isEmpty then
    println! "No builtin checkpoints are required for the GPT-5-mini-only release."
  else
    println! "Done!"
