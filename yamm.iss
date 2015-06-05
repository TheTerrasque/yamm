; Script generated by the Inno Script Studio Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "YAMM"
#define MyAppVersion "0.1"
#define MyAppPublisher "Terrasque"
#define MyAppURL "https://github.com/TheTerrasque/yamm"
#define MyAppExeName "yammy ui.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{F03798C2-DDB0-4A4F-A725-7905C6AE3B85}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=setup_yamm
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "yammurlhandler"; Description: "Setup YAMM link handling"; GroupDescription: "System Integration"
Name: "moplugin"; Description: "Install Mod Organizer (v1.3.5+) plugin"; GroupDescription: "System Integration"

[Files]
Source: "dist\yammy ui\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Parameters: "--setup"; Tasks: moplugin

[Registry]
Root: HKCR; Subkey: "yamm"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""; Tasks: yammurlhandler
Root: HKCR; Subkey: "yamm"; ValueType: string; ValueName: ""; ValueData: "URL:yamm"; Tasks: yammurlhandler
Root: HKCR; Subkey: "yamm\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --url ""%1"""; Tasks: yammurlhandler