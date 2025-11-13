import LeanCopilot.Models.External

set_option autoImplicit false

namespace LeanCopilot.Builtin

/--
Default external generator configuration used throughout Lean Copilot.
This points to the Python server (localhost:23337) and requests GPT-5-nano.
-/
def generator : ExternalGenerator where
  name := "gpt-5-nano"
  host := "localhost"
  port := 23337

end LeanCopilot.Builtin
