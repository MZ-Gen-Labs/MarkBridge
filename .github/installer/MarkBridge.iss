; MarkBridge Inno Setup Script
; This script creates a Windows installer for MarkBridge

#define MyAppName "MarkBridge"
#define MyAppPublisher "MZ-Gen-Labs"
#define MyAppURL "https://github.com/MZ-Gen-Labs/MarkBridge"
#define MyAppExeName "MarkBridge.exe"

[Setup]
; 固定のAppId - 同じIDを使うことで上書きインストールが可能
AppId={{8A4D6F2E-3B5C-4A1D-9E8F-7C2B1A0D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; アップグレード時に旧バージョンの場所を使用
UsePreviousAppDir=yes
UsePreviousGroup=yes
UsePreviousLanguage=yes
UsePreviousTasks=yes
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
; インストーラー出力先
OutputDir=..\..\installer
OutputBaseFilename=MarkBridge-{#MyAppVersion}-win-x64-setup
; 圧縮設定
Compression=lzma2/ultra64
SolidCompression=yes
; モダンUI
WizardStyle=modern
; セットアップアイコン（GitHub ActionsでPNGからICOに変換される）
SetupIconFile=..\..\Resources\AppIcon\appicon.ico
; 64ビット専用
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
; 権限設定（ユーザー単位インストール可能）
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; アップグレード機能
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=yes
; アンインストール時に古いファイルを削除
UninstallFilesDir={app}\uninstall
; バージョン情報
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoCopyright=Copyright (C) 2024 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; アプリケーションファイル（再帰的にコピー、変更されたファイルのみ更新）
Source: "..\..\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; アンインストール時にログファイル等を削除
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\cache"

[Code]
// アップグレードインストール時に旧バージョンをアンインストール
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;

// アップグレード時にメッセージを表示
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    if IsUpgrade() then
    begin
      Log('Performing upgrade installation...');
    end;
  end;
end;
