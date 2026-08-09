; Inno Setup script — FinSight Windows installer.
;
; Build (on Windows, after `pyinstaller build\windows\finsight.spec` has produced dist\FinSight):
;     iscc build\windows\finsight.iss
; Produces dist\FinSight-2.0.0-Setup.exe
;
; Per-user installation by design. FinSight stores its encrypted review data under the signed-in
; account (%LOCALAPPDATA%\FinSight) and protects its store key with per-user DPAPI, so neither the
; install nor the first run needs an administrator. That keeps a client tester's machine untouched
; outside their own profile.

#define AppName        "FinSight"
#define AppVersion     "2.0.0"
#define AppPublisher   "FinSight"
#define AppExeName     "FinSight.exe"

[Setup]
; Stable identity for Programs & Features and for upgrade-in-place over a previous version.
AppId={{8B4E0F42-6C31-4A7D-9E15-2F7A6C0B3D58}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersion}

; lowest => no UAC prompt, no administrator required.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes

OutputDir=..\..\dist
OutputBaseFilename={#AppName}-{#AppVersion}-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=finsight.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

; The PyInstaller one-dir build is x64-only (the pinned sqlcipher3/cryptography/PySide6 wheels are
; win_amd64), so refuse to install on an architecture the payload cannot run on.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; Ask Fin is optional. FinSight's deterministic review runs with no AI provider at all (FR-095),
; so this task is unchecked by default: the product installs and works fully without it, and a
; machine with no internet connection is never blocked from installing FinSight.
Name: "askfin"; Description: "Set up Ask Fin (downloads the local AI runtime, about 2 GB)"; GroupDescription: "Optional assistant:"; Flags: unchecked

[Files]
; The complete PyInstaller one-dir output: FinSight.exe plus the Qt runtime, the Python runtime,
; the self-contained sqlcipher3 extension, and the QtAwesome icon fonts.
Source: "..\..\dist\FinSight\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Provisioning helper, installed so the optional assistant can also be set up after installation
; without the user ever opening a terminal.
Source: "provision_ask_fin.ps1"; DestDir: "{app}\setup"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
; -NoExit keeps the result readable: provisioning downloads about 2 GB and the user should be
; able to see whether it finished before the window closes.
Name: "{group}\Set up Ask Fin"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -NoExit -File ""{app}\setup\provision_ask_fin.ps1"""; IconFilename: "{app}\{#AppExeName}"; Comment: "Install the optional local AI assistant"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Optional assistant provisioning. Runs only when the user ticked the task.
; The trailing `exit 0` is deliberate: the assistant is optional, so a provisioning failure (no
; network, declined runtime install, model download interrupted) must NOT make a successful
; FinSight installation report itself as failed. The script's real exit code still surfaces when
; it is re-run from the Start Menu entry above.
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; \
    Parameters: "-ExecutionPolicy Bypass -NoProfile -Command ""& '{app}\setup\provision_ask_fin.ps1'; exit 0"""; \
    StatusMsg: "Setting up Ask Fin (this can take several minutes)..."; \
    Flags: waituntilterminated runhidden; Tasks: askfin
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove only what the installer created. Review data, the audit trail, and the disposal registry
; under %LOCALAPPDATA%\FinSight are deliberately left in place: FinSight's retention model is
; non-destructive, and an uninstall must never silently destroy a reviewer's financial history.
; Removing that directory is an explicit, separate operator action.
Type: filesandordirs; Name: "{app}"
