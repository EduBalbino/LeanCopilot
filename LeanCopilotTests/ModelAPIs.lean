import LeanCopilot

open LeanCopilot

/--
Example of a custom generator implemented directly in Lean.
-/
def dummyGenerator : GenericGenerator where
  generate _ _ := return #[⟨"exact rfl", 0.5⟩, ("trivial", 0.3)]

#eval generate dummyGenerator "n : ℕ\n⊢ n = n"


/--
Example of a custom encoder implemented directly in Lean.
-/
def dummyEncoder : GenericEncoder where
  encode _ := return FloatArray.mk #[1, 2, 3]

#eval encode dummyEncoder "Hello"


/--
Default GPT-5 endpoint exposed by the bundled FastAPI server.
-/
def gpt5Mini : ExternalGenerator := {
  name := "gpt-5-mini"
  host := "localhost"
  port := 23337
}

#eval generate gpt5Mini "n : ℕ\n⊢ gcd n n = n"


/--
External encoder backed by the Python server. Useful for premise selection
when the server implements the `/encode` endpoint.
-/
def externalEncoder : ExternalEncoder := {
  name := "kaiyuy/leandojo-lean4-retriever-byt5-small"
  host := "localhost"
  port := 23337
}

#eval encode externalEncoder "n : ℕ\n⊢ gcd n n = n"
