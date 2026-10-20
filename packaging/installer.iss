#define AppName "GAS HUNAR"
#define AppVersion "0.2.0"
[Setup]
AppId={{7702833F-448C-4E42-9459-635A202C99A4}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=GAS HUNAR
DefaultDirName={localappdata}\Programs\GAS HUNAR
DefaultGroupName=GAS HUNAR
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=GAS HUNAR Setup
SetupIconFile=..\assets\gas-hunar.ico
UninstallDisplayIcon={app}\GAS HUNAR.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked
[Files]
Source: "..\dist\GAS HUNAR.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\FONT-LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\GAS HUNAR"; Filename: "{app}\GAS HUNAR.exe"
Name: "{autodesktop}\GAS HUNAR"; Filename: "{app}\GAS HUNAR.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\GAS HUNAR.exe"; Description: "Launch GAS HUNAR"; Flags: nowait postinstall skipifsilent
; Deliberately no [UninstallDelete] rule. Restaurant data remains in LocalAppData\GAS HUNAR.
