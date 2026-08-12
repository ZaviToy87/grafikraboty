; Inno Setup Script for GrafikRaboty v4.9
; Создаёт полноценный установщик Windows

#define MyAppName "GrafikRaboty"
#define MyAppVersion "4.9"
#define MyAppPublisher "VetGid"
#define MyAppExeName "GrafikRaboty_Server.exe"

[Setup]
; Основные настройки
AppId={{A3B5C7D9-1234-5678-90AB-CDEF12345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=http://vetgid.ru
AppSupportURL=http://vetgid.ru/support
AppUpdatesURL=http://vetgid.ru/updates

; Пути установки
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=installer_output
OutputBaseFilename=GrafikRaboty_Setup_v4.9
SetupIconFile=
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Права доступа
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Минимальная версия Windows
MinVersion=10.0.18362

; Язык
LanguageDetectionMethod=locale
UsePreviousLanguage=no
DefaultLanguageName=Russian

; Настройки страниц
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
DisableReadyPage=no

; Проверка места на диске
ExtraDiskSpaceRequired=600000000

[Files]
; Исходные файлы из папки exe_dist\GrafikRaboty_Server
Source: "exe_dist\GrafikRaboty_Server\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "exe_dist\GrafikRaboty_Server\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs
Source: "exe_dist\GrafikRaboty_Server\.mcp\*"; DestDir: "{app}\.mcp"; Flags: ignoreversion recursesubdirs
Source: "exe_dist\GrafikRaboty_Server\logs\*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs
Source: "exe_dist\GrafikRaboty_Server\static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs
Source: "exe_dist\GrafikRaboty_Server\templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs
Source: "exe_dist\GrafikRaboty_Server\uploads\*"; DestDir: "{app}\uploads"; Flags: ignoreversion recursesubdirs

[Icons]
; Ярлыки в меню Пуск
Name: "{group}\{#MyAppName}"; Filename: "{app}\RUN.bat"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Запустить сервер"; Filename: "{app}\RUN.bat"
Name: "{group}\Открыть в браузере"; Filename: "http://localhost:8080"
Name: "{group}\Папка установки"; Filename: "{app}"
Name: "{group}\Справка"; Filename: "{app}\README_EXE.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Ярлык на рабочем столе
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\RUN.bat"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
; Запуск после установки
Filename: "{app}\RUN.bat"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked

[Code]
// Проверка порта 8080
function IsPort8080Free: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('netstat', '-ano | findstr :8080', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := (ResultCode <> 0);
end;

// Проверка перед установкой
function InitializeSetup: Boolean;
var
  ResultCode: Integer;
begin
  if not IsPort8080Free then
  begin
    if MsgBox('Порт 8080 занят! Другая программа использует этот порт.' + #13#10 + #13#10 + 'Продолжить установку?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  Result := True;
end;

// После установки
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Копирование конфигов по умолчанию если их нет
    if not FileExists(ExpandConstant('{app}\telegram_config.json')) then
    begin
      SaveStringToFile(ExpandConstant('{app}\telegram_config.json'),
        '{' + #13#10 +
        '  "token": "YOUR_BOT_TOKEN",' + #13#10 +
        '  "chat_ids": [701768868],' + #13#10 +
        '  "admin_user_id": 701768868' + #13#10 +
        '}', False);
    end;
    
    if not FileExists(ExpandConstant('{app}\vk_config.json')) then
    begin
      SaveStringToFile(ExpandConstant('{app}\vk_config.json'),
        '{' + #13#10 +
        '  "token": "VK_SERVICE_TOKEN",' + #13#10 +
        '  "group_id": 199112265,' + #13#10 +
        '  "chat_peer_id": 2000000001' + #13#10 +
        '}', False);
    end;
  end;
end;

// Страница с инструкцией
procedure InitializeWizard;
var
  InfoPage: TWizardPage;
  InfoMemo: TMemo;
begin
  InfoPage := CreateCustomPage(wpWelcome, 'Добро пожаловать', 'Инструкция по установке');
  
  InfoMemo := TMemo.Create(InfoPage);
  InfoMemo.Parent := InfoPage.Surface;
  InfoMemo.Width := InfoPage.SurfaceWidth;
  InfoMemo.Height := InfoPage.SurfaceHeight;
  InfoMemo.ReadOnly := True;
  InfoMemo.ScrollBars := ssVertical;
  
  InfoMemo.Text :=
    'Добро пожаловать в мастер установки GrafikRaboty v4.9!' + #13#10 + #13#10 +
    'Эта программа установит корпоративный график ВетГид на ваш компьютер.' + #13#10 + #13#10 +
    'Что будет установлено:' + #13#10 +
    '  • Веб-сервер (порт 8080)' + #13#10 +
    '  • MCP система (порт 8081)' + #13#10 +
    '  • База данных' + #13#10 +
    '  • Telegram бот' + #13#10 +
    '  • VK интеграция' + #13#10 + #13#10 +
    'Требования:' + #13#10 +
    '  • Windows 10/11' + #13#10 +
    '  • 600 MB свободного места' + #13#10 +
    '  • Свободные порты 8080 и 8081' + #13#10 + #13#10 +
    'Нажмите "Далее" для продолжения установки.';
end;

// Финальная страница
procedure CurPageChanged(CurPageID: Integer);
var
  FinalMemo: TMemo;
  Page: TWizardPage;
begin
  if CurPageID = wpReady then
  begin
    // Показать информацию перед установкой
  end;
  
  if CurPageID = wpFinished then
  begin
    // Создать финальную страницу с инструкциями
    Page := CreateCustomPage(wpFinished, 'Установка завершена', 'Что делать дальше');
    
    FinalMemo := TMemo.Create(Page);
    FinalMemo.Parent := Page.Surface;
    FinalMemo.Width := Page.SurfaceWidth;
    FinalMemo.Height := Page.SurfaceHeight;
    FinalMemo.ReadOnly := True;
    FinalMemo.ScrollBars := ssVertical;
    
    FinalMemo.Text :=
      'Установка GrafikRaboty v4.9 успешно завершена!' + #13#10 + #13#10 +
      'Следующие шаги:' + #13#10 + #13#10 +
      '1. Заполните конфигурационные файлы:' + #13#10 +
      '   • telegram_config.json — токен Telegram бота' + #13#10 +
      '   • vk_config.json — токен VK группы' + #13#10 + #13#10 +
      '2. Запустите сервер:' + #13#10 +
      '   • Через ярлык на рабочем столе' + #13#10 +
      '   • Или через Пуск → GrafikRaboty → Запустить сервер' + #13#10 + #13#10 +
      '3. Откройте в браузере:' + #13#10 +
      '   http://localhost:8080' + #13#10 + #13#10 +
      'Учётные данные по умолчанию:' + #13#10 +
      '   Логин: admin' + #13#10 +
      '   Пароль: admin' + #13#10 + #13#10 +
      'Для справки откройте файл README_EXE.md в папке установки.';
  end;
end;

[Languages]
Name: "russian"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Добро пожаловать в мастер установки GrafikRaboty v4.9
SetupAppTitle=Установка GrafikRaboty

[CustomMessages]
LaunchProgram=Запустить GrafikRaboty
