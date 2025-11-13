import LeanCopilot

open LeanCopilot

/--
Local alias for the default GPT-5-mini generator served by `python/server.py`.
Update `host`/`port` if you run the server elsewhere.
-/
def gpt5MiniLocal : Generator :=
  {Builtin.generator with
    host := "localhost"
    port := 23337
  }


/-
Once the Python server is live you can generate tactics directly:

#eval registerGenerator "gpt-5-mini-local" gpt5MiniLocal
#eval generate gpt5MiniLocal "n : ℕ\n⊢ gcd n n = n"

The evaluation is commented out by default so CI does not make external requests.
-/
