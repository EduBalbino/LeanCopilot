import LeanCopilot

open LeanCopilot

/--
Local alias for the default GPT-5-nano generator served by `python/server.py`.
Update `host`/`port` if you run the server elsewhere.
-/
def gpt5NanoLocal : Generator :=
  ({Builtin.generator with
    host := "localhost"
    port := 23337
  } : ExternalGenerator)


/-
Once the Python server is live you can generate tactics directly:

#eval registerGenerator "gpt-5-nano-local" gpt5NanoLocal
#eval generate gpt5NanoLocal "n : ℕ\n⊢ gcd n n = n"

The evaluation is commented out by default so CI does not make external requests.
-/
