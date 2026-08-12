; =============================================================================
; GRAFIKRABOTY v4.9 — Установочный скрипт Inno Setup
; Создаёт полноценный EXE установщик со всеми компонентами
; =============================================================================

#define MyAppName "GrafikRaboty"
#define MyAppVersion "4.9"
#define MyAppPublisher "VetGid Corporation"
#define MyAppURL "http://vetgid.ru"
#define MyAppExeName "GrafikRaboty_Server.exe"
#define MyIconFile "static\images\vetgid-logo.png"

[Setup]
; Основные настройки установщика
AppId={{7F8B5C3A-9D2E-4F1B-8C6A-3E5D7F9B1A2C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/updates

; Пути установки
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
DisableProgramGroupPage=yes

; Сжатие и компиляция
Compression=lzma2/max
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMADictionarySize=1048576
LZMANumFastBytes=273
WizardStyle=modern

; Иконка установщика
SetupIconFile=compiler:SetupClassicIcon.ico

; Права доступа
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline

; Минимальная Windows
MinVersion=10.0.18362

; Проверка места
ExtraDiskSpaceRequired=600000000

; Язык
LanguageDetectionMethod=uilanguage
UsePreviousLanguage=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
; === ОСНОВНЫЕ ФАЙЛЫ ===
Source: "installer_build\GrafikRaboty_Server.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_build\RUN.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_build\Start_MCP_Server.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_build\README_EXE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_build\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; === БАЗЫ ДАННЫХ ===
Source: "installer_build\schedule.db"; DestDir: "{app}"; Flags: ignoreversion

; === КОНФИГУРАЦИИ ===
Source: "installer_build\telegram_config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_build\vk_config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_build\telegram_seen_users.json"; DestDir: "{app}"; Flags: ignoreversion

; === MCP СИСТЕМА ===
Source: "installer_build\.mcp\*"; DestDir: "{app}\.mcp"; Flags: ignoreversion recursesubdirs createallsubdirs

; === ШАБЛОНЫ ===
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs

; === СТАТИКА ===
Source: "static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs

; === ЗАГРУЗКИ ===
Source: "uploads\*"; DestDir: "{app}\uploads"; Flags: ignoreversion recursesubdirs createallsubdirs

; === ВНУТРЕННИЕ ФАЙЛЫ PYINSTALLER ===
Source: "installer_build\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; === ЛОГИ ===
Source: "installer_build\logs\*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; === ЯРЛЫКИ В МЕНЮ ПУСК ===
Name: "{group}\{#MyAppName}"; Filename: "{app}\RUN.bat"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0; Comment: "Запустить сервер GrafikRaboty"
Name: "{group}\Запустить сервер"; Filename: "{app}\RUN.bat"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0
Name: "{group}\Открыть в браузере"; Filename: "http://localhost:8080"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0
Name: "{group}\Папка установки"; Filename: "{app}"
Name: "{group}\Логи"; Filename: "{app}\logs"
Name: "{group}\Справка"; Filename: "{app}\README_EXE.md"
Name: "{group}\Настройки Telegram"; Filename: "{app}\telegram_config.json"
Name: "{group}\Настройки VK"; Filename: "{app}\vk_config.json"
Name: "{uninstallexe}\{#MyAppName}"; Filename: "{uninstallexe}"

; === ЯРЛЫК НА РАБОЧЕМ СТОЛЕ (с выбором при установке) ===
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\RUN.bat"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0; Tasks: desktopicon

[Tasks]
; === ЗАДАЧИ УСТАНОВКИ ===
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: unchecked
Name: "autostart"; Description: "Запускать сервер автоматически при загрузке Windows"; GroupDescription: "Автозагрузка:"; Flags: unchecked
Name: "startmenuicon"; Description: "Создать ярлыки в меню Пуск"; GroupDescription: "Ярлыки в меню Пуск:"; Flags: unchecked

[Run]
; === ЗАПУСК ПОСЛЕ УСТАНОВКИ ===
Filename: "{app}\RUN.bat"; Description: "Запустить GrafikRaboty"; Flags: nowait postinstall skipifsilent unchecked

[Code]
// =============================================================================
// ПРОГРАММНЫЙ КОД УСТАНОВЩИКА
// =============================================================================

var
  PortCheckResult: Integer;
  CustomPage: TWizardPage;
  Memo: TMemo;

// -----------------------------------------------------------------------------
// Проверка порта 8080
// -----------------------------------------------------------------------------
function IsPort8080Free: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('netstat', '-ano | findstr :8080', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := (ResultCode <> 0);
end;

// -----------------------------------------------------------------------------
// Проверка перед установкой
// -----------------------------------------------------------------------------
function InitializeSetup: Boolean;
begin
  if not IsPort8080Free then
  begin
    if MsgBox('⚠️ Порт 8080 занят другой программой!' + #13#10 + #13#10 +
              'Это может помешать работе GrafikRaboty.' + #13#10 +
              'Продолжить установку?', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  Result := True;
end;

// -----------------------------------------------------------------------------
// Создание информационной страницы
// -----------------------------------------------------------------------------
procedure InitializeWizard;
begin
  CustomPage := CreateCustomPage(wpWelcome, 'Добро пожаловать в GrafikRaboty', 'Информация о программе');

  Memo := TMemo.Create(CustomPage);
  Memo.Parent := CustomPage.Surface;
  Memo.Width := CustomPage.SurfaceWidth;
  Memo.Height := CustomPage.SurfaceHeight;
  Memo.ReadOnly := True;
  Memo.ScrollBars := ssVertical;
  Memo.Font.Size := 10;

  Memo.Text :=
    '🎉 Добро пожаловать в мастер установки GrafikRaboty v4.9!' + #13#10 + #13#10 +
    '📋 Описание:' + #13#10 +
    '   Корпоративная система управления графиком работы' + #13#10 +
    '   для сети магазинов ВетГид.' + #13#10 + #13#10 +
    '📦 Что будет установлено:' + #13#10 +
    '   ✓ Веб-сервер (порт 8080)' + #13#10 +
    '   ✓ MCP система с 9 агентами (порт 8081)' + #13#10 +
    '   ✓ База данных SQLite' + #13#10 +
    '   ✓ Telegram бот для уведомлений' + #13#10 +
    '   ✓ VK интеграция для чата' + #13#10 +
    '   ✓ Рабочий журнал' + #13#10 +
    '   ✓ Конвертер ценников' + #13#10 +
    '   ✓ Генератор штрих-кодов' + #13#10 +
    '   ✓ Админ-панель' + #13#10 + #13#10 +
    '💻 Требования:' + #13#10 +
    '   ✓ Windows 10/11' + #13#10 +
    '   ✓ 600 MB свободного места' + #13#10 +
    '   ✓ Свободные порты 8080 и 8081' + #13#10 + #13#10 +
    '⚙️ На следующем этапе вы сможете:' + #13#10 +
    '   • Выбрать папку для установки' + #13#10 +
    '   • Создать ярлык на рабочем столе' + #13#10 +
    '   • Настроить автозагрузку' + #13#10 + #13#10 +
    'Нажмите "Далее" для продолжения установки.';
end;

// -----------------------------------------------------------------------------
// После установки
// -----------------------------------------------------------------------------
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Создание шаблонов конфигов если их нет
    ConfigPath := ExpandConstant('{app}\telegram_config.json');
    if not FileExists(ConfigPath) then
    begin
      SaveStringToFile(ConfigPath,
        '{' + #13#10 +
        '  "token": "8755572729:AAGAvyRp6Uni_wCbwjGIe2WRLOPUSlQ3iAc",' + #13#10 +
        '  "chat_ids": [701768868],' + #13#10 +
        '  "admin_user_id": 701768868' + #13#10 +
        '}', False);
    end;

    ConfigPath := ExpandConstant('{app}\vk_config.json');
    if not FileExists(ConfigPath) then
    begin
      SaveStringToFile(ConfigPath,
        '{' + #13#10 +
        '  "token": "VK_SERVICE_TOKEN",' + #13#10 +
        '  "group_id": 199112265,' + #13#10 +
        '  "chat_peer_id": 2000000001' + #13#10 +
        '}', False);
    end;

    // Добавление в автозагрузку если выбрано
    if IsTaskSelected('autostart') then
    begin
      RegWriteStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run',
        '{#MyAppName}', ExpandConstant('{app}\RUN.bat'));
    end;
  end;
end;

// -----------------------------------------------------------------------------
// Финальная страница
// -----------------------------------------------------------------------------
procedure CurPageChanged(CurPageID: Integer);
var
  FinalMemo: TMemo;
  Page: TWizardPage;
begin
  if CurPageID = wpFinished then
  begin
    Page := CreateCustomPage(wpFinished, 'Установка завершена!', 'Следующие шаги');

    FinalMemo := TMemo.Create(Page);
    FinalMemo.Parent := Page.Surface;
    FinalMemo.Width := Page.SurfaceWidth;
    FinalMemo.Height := Page.SurfaceHeight;
    FinalMemo.ReadOnly := True;
    FinalMemo.ScrollBars := ssVertical;
    FinalMemo.Font.Size := 10;

    FinalMemo.Text :=
      '✅ Установка GrafikRaboty v4.9 успешно завершена!' + #13#10 + #13#10 +
      '📋 Следующие шаги:' + #13#10 + #13#10 +
      '1️⃣ Заполните конфигурационные файлы:' + #13#10 +
      '   • telegram_config.json — токен Telegram бота' + #13#10 +
      '   • vk_config.json — токен VK группы' + #13#10 + #13#10 +
      '2️⃣ Запустите сервер:' + #13#10 +
      '   • Через ярлык на рабочем столе' + #13#10 +
      '   • Через Пуск → GrafikRaboty → Запустить сервер' + #13#10 + #13#10 +
      '3️⃣ Откройте в браузере:' + #13#10 +
      '   http://localhost:8080' + #13#10 + #13#10 +
      '🔐 Учётные данные по умолчанию:' + #13#10 +
      '   Логин: admin' + #13#10 +
      '   Пароль: admin' + #13#10 + #13#10 +
      '📚 Документация:' + #13#10 +
      '   • README_EXE.md в папке установки' + #13#10 +
      '   • http://vetgid.ru/docs' + #13#10 + #13#10 +
      '🎉 Приятной работы с GrafikRaboty!';
  end;
end;

// -----------------------------------------------------------------------------
// Проверка запускаемой программы
// -----------------------------------------------------------------------------
function IsRunning: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('tasklist', '/FI "IMAGENAME eq GrafikRaboty_Server.exe" /NH', '',
    SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := (ResultCode = 0);
end;

// -----------------------------------------------------------------------------
// Перед установкой
// -----------------------------------------------------------------------------
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  if IsRunning then
  begin
    if MsgBox('Сервер GrafikRaboty уже запущен!' + #13#10 + #13#10 +
              'Закрыть его для установки?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec('taskkill', '/F /IM GrafikRaboty_Server.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end
    else
    begin
      Result := 'Закройте GrafikRaboty_Server.exe вручную и повторите установку.';
    end;
  end;
end;

[UninstallDelete]
; === ОЧИСТКА ПРИ УДАЛЕНИИ ===
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\uploads"
Type: filesandordirs; Name: "{app}\_internal"

[UninstallRun]
; === ОСТАНОВКА СЕРВЕРА ПРИ УДАЛЕНИИ ===
Filename: "taskkill"; Parameters: "/F /IM GrafikRaboty_Server.exe"; Flags: runhidden
Filename: "taskkill"; Parameters: "/F /IM python.exe"; Flags: runhidden

[Registry]
; === РЕЕСТР ===
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: dword; ValueName: "Port"; ValueData: "8080"; Flags: uninsdeletekey

[Messages]
WelcomeLabel1=Добро пожаловать в мастер установки GrafikRaboty v4.9
WelcomeLabel2=Эта программа установит GrafikRaboty на ваш компьютер.%n%nРекомендуется закрыть все работающие приложения перед продолжением.%n%nНажмите "Далее" для продолжения.
SelectTasksLabel1=Выберите дополнительные задачи:
SelectTasksLabel2=Выберите задачи для выполнения во время установки:
SelectDirLabel3=Выберите папку для установки GrafikRaboty:
ReadyLabel1=Готов к установке GrafikRaboty v4.9
ReadyLabel2=Нажмите "Установить" для начала установки или "Назад" для изменения параметров.

[CustomMessages]
LaunchProgram=Запустить GrafikRaboty
DesktopIcon=Создать ярлык на &рабочем столе
QuickLaunchIcon=Создать ярлык в &панели быстрого запуска
AutoStartTask=Запускать при &загрузке Windows
StartMenuIcon=Создать ярлыки в &меню Пуск
