import LeanCopilot.Models.External

set_option autoImplicit false

namespace LeanCopilot.Builtin

/--
Default external generator pointing at the bundled FastAPI server.
-/
def generator : ExternalGenerator := {
  name := "gpt-5-mini"
  host := "localhost"
  port := 23337
}

/--
Default external encoder used by `select_premises`. The server may choose to
return a placeholder vector if it does not support encoders.
-/
def encoder : ExternalEncoder := {
  name := "kaiyuy/leandojo-lean4-retriever-byt5-small"
  host := "localhost"
  port := 23337
}

end LeanCopilot.Builtin
