import Lake

open Lake DSL System Lean Elab

set_option autoImplicit false


inductive SupportedOS where
  | linux
  | macos
  | windows
deriving Inhabited, BEq


def getOS! : SupportedOS :=
  if Platform.isWindows then
     .windows
  else if Platform.isOSX then
     .macos
  else
     .linux


inductive SupportedArch where
  | x86_64
  | arm64
deriving Inhabited, BEq


def nproc : IO Nat := do
  let cmd := if getOS! == .windows then "cmd" else "nproc"
  let args := if getOS! == .windows then #["/c echo %NUMBER_OF_PROCESSORS%"] else #[]
  let out ← IO.Process.output {cmd := cmd, args := args, stdin := .null}
  return out.stdout.trim.toNat!


def getArch? : IO (Option SupportedArch) := do
  let cmd := if getOS! == .windows then "cmd" else "uname"
  let args := if getOS! == .windows then #["/c echo %PROCESSOR_ARCHITECTURE%\n"] else #["-m"]

  let out ← IO.Process.output {cmd := cmd, args := args, stdin := .null}
  let arch := out.stdout.trim

  if arch ∈ ["arm64", "aarch64", "ARM64"] then
    return some .arm64
  else if arch ∈ ["x86_64", "AMD64"] then
    return some .x86_64
  else
    return none


def getArch! : IO SupportedArch := do
  if let some arch ← getArch? then
    return arch
  else
    error "Unknown architecture"


def isArm! : IO Bool := do
  return (← getArch!) == .arm64


def hasCUDA : IO Bool := do
  if getOS! == .windows then
    let ok ← testProc {
      cmd := "nvidia-smi"
      args := #[]
    }
    return ok
  else
    let out ← IO.Process.output {cmd := "which", args := #["nvcc"], stdin := .null}
    return out.exitCode == 0

def useCUDA : IO Bool := do
  return (get_config? noCUDA |>.isNone) ∧ (← hasCUDA)


def buildArchiveName : String :=
  let arch := if run_io isArm! then "arm64" else "x86_64"
  let os := if getOS! == .macos then "macOS" else "linux"
  if run_io useCUDA then
    s!"{arch}-cuda-{os}.tar.gz"
  else
    s!"{arch}-{os}.tar.gz"


structure SupportedPlatform where
  os : SupportedOS
  arch : SupportedArch


def getPlatform! : IO SupportedPlatform := do
  if Platform.numBits != 64 then
    error "Only 64-bit platforms are supported"
  return ⟨getOS!, ← getArch!⟩

def copySingleFile (src dst : FilePath) : LogIO Unit := do
  let cmd := if getOS! == .windows then "cmd" else "cp"
  let args :=
    if getOS! == .windows then
      #[s!"/c copy {src.toString.replace "/" "\\"} {dst.toString.replace "/" "\\"}"]
    else
      #[src.toString, dst.toString]

  proc {
    cmd := cmd
    args := args
  }

def copyFolder (src dst : FilePath) : LogIO Unit := do
  let cmd := if getOS! == .windows then "robocopy" else "cp"
  let args :=
    if getOS! == .windows then
      #[src.toString, dst.toString, "/E"]
    else
      #["-r", src.toString, dst.toString]

  let _out ← rawProc {
    cmd := cmd
    args := args
  }

def removeFolder (dir : FilePath) : LogIO Unit := do
  let cmd := if getOS! == .windows then "cmd" else "rm"
  let args :=
    if getOS! == .windows then
      #[s!"/c rmdir /s /q {dir.toString.replace "/" "\\"}"]
    else
      #["-rf", dir.toString]

  proc {
    cmd := cmd
    args := args
  }

def removeFile (src: FilePath) : LogIO Unit := do
  proc {
    cmd := if getOS! == .windows then "cmd" else "rm"
    args := if getOS! == .windows then #[s!"/c del {src.toString.replace "/" "\\"}"] else #[src.toString]
  }

package LeanCopilot where
  preferReleaseBuild := get_config? noCloudRelease |>.isNone
  buildArchive? := buildArchiveName
  precompileModules := true
  buildType := BuildType.release


@[default_target]
lean_lib LeanCopilot {
}


lean_lib ModelCheckpointManager {
}


lean_exe download {
  root := `ModelCheckpointManager.Main
}


lean_lib LeanCopilotTests {
  globs := #[.submodules "LeanCopilotTests".toName]
}


-- Internal generators and premise-selection code have been removed,
-- so we no longer build or link against the legacy CTranslate2 FFI.


require batteries from git "https://github.com/leanprover-community/batteries.git" @ "main"
require aesop from git "https://github.com/leanprover-community/aesop" @ "master"

meta if get_config? env = some "dev" then -- dev is so not everyone has to build it
require «doc-gen4» from git "https://github.com/leanprover/doc-gen4" @ "main"
