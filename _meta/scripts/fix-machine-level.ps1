<#
    fix-machine-level.ps1
    ------------------------------------------------------------------
    需要管理员权限。处理两项本会话无法完成的机器级改动：

      [1] 清理系统 PATH（HKLM）
          - 删除无效条目：...\pandoc-3.8.2\pandoc-3.8.2\pandoc.exe
            （PATH 中指向文件而非目录，Windows 不会用于命令解析；
              用户级 PATH 已有可用的 Pandoc 3.8.3）
          - 删除重复条目：C:\msys64\ucrt64\bin\（与 C:\msys64\ucrt64\bin 同一目录）

      [2] 用 22.23.2 的 MSI 重装 Node.js
          - 现状：注册表 DisplayVersion = 22.17.1，实际 node.exe = 22.23.2（原地升级导致）
          - 目标：让注册表 / MSI 缓存与真实版本一致
          - 安装目录保持 C:\nodejs（与现有安装一致，避免产生第二份 Node）

    用法：右键“以管理员身份运行 PowerShell”，然后
          powershell -ExecutionPolicy Bypass -File D:\Code_practice\fix-machine-level.ps1

    回滚：脚本运行前会把原始 PATH 备份到 D:\Code_practice\backup\，
          Node 如需回退可重装 22.17.1 的 MSI。
#>

$ErrorActionPreference = 'Stop'
$BackupDir = 'D:\Code_practice\backup'
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Assert-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Host "[X] 未以管理员身份运行。请右键 PowerShell -> 以管理员身份运行后重试。" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] 已获得管理员权限 ($($id.Name))" -ForegroundColor Green
}

function Send-SettingChange {
    if (-not ('W32.NM' -as [type])) {
        Add-Type -Namespace W32 -Name NM -MemberDefinition @'
[DllImport("user32.dll", SetLastError=true, CharSet=CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
'@
    }
    $r = [UIntPtr]::Zero
    [void][W32.NM]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, "Environment", 2, 5000, [ref]$r)
}

# ==================================================================
# [1] 系统 PATH 清理
# ==================================================================
function Repair-MachinePath {
    Write-Host "`n===== [1/2] 清理系统 PATH =====" -ForegroundColor Cyan

    $key = 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    $old = (Get-ItemProperty $key -Name Path).Path

    $bak = Join-Path $BackupDir "machine-PATH-BEFORE-REPAIR-$Stamp.txt"
    Set-Content -Path $bak -Value $old -Encoding UTF8
    Write-Host "[备份] $bak"

    # 无效条目：PATH 中指向文件而非目录
    $removeExact = @(
        'C:\Program Files (x86)\pandoc-3.8.2\pandoc-3.8.2\pandoc.exe'
    )

    $entries = @($old -split ';' | Where-Object { $_ -ne '' })
    $kept    = @()
    $seenDir = @{}   # 归一化后的目录，用于识别尾随反斜杠造成的重复

    foreach ($e in $entries) {
        if ($removeExact -contains $e) {
            Write-Host "  [删除-无效] $e" -ForegroundColor Yellow
            continue
        }

        # 归一化：去掉尾部反斜杠后比较；同时对已判定为无效的文件型条目做二次拦截
        $norm = $e.TrimEnd('\')
        if (-not (Test-Path $e -PathType Container)) {
            if (Test-Path $e -PathType Leaf) {
                Write-Host "  [删除-文件项] $e" -ForegroundColor Yellow
                continue
            }
            Write-Host "  [保留-不存在] $e" -ForegroundColor DarkYellow
        }

        if ($seenDir.ContainsKey($norm)) {
            Write-Host "  [删除-重复] $e  (与 '$($seenDir[$norm])' 同一目录)" -ForegroundColor Yellow
            continue
        }
        $seenDir[$norm] = $e
        $kept += $e
    }

    $new = ($kept -join ';')

    if ($new -eq $old) {
        Write-Host "  (无需改动)" -ForegroundColor DarkGray
        return
    }

    # 保持原来的值类型（REG_EXPAND_SZ）
    Set-ItemProperty -Path $key -Name Path -Value $new -Type ExpandString
    Send-SettingChange

    Write-Host "`n[完成] 条目数 $($entries.Count) -> $($kept.Count)" -ForegroundColor Green
    Write-Host "--- 新的系统 PATH ---"
    $i = 0; $kept | ForEach-Object { $i++; "  {0,2}. {1}" -f $i, $_ }
}

# ==================================================================
# [2] Node.js MSI 重装
# ==================================================================
function Repair-NodeRegistry {
    Write-Host "`n===== [2/2] 重装 Node.js (MSI) =====" -ForegroundColor Cyan

    $targetVer = '22.23.2'
    $installDir = 'C:\nodejs'
    $msiUrl = "https://nodejs.org/dist/v$targetVer/node-v$targetVer-x64.msi"
    $msiPath = Join-Path $env:TEMP "node-v$targetVer-x64.msi"

    # --- 现状 ---
    $nodeExe = Join-Path $installDir 'node.exe'
    $realVer = if (Test-Path $nodeExe) { (Get-Item $nodeExe).VersionInfo.ProductVersion } else { '(未找到)' }
    $regKey = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
              Where-Object { $_.DisplayName -like 'Node.js*' }
    Write-Host "  当前注册表版本 : $($regKey.DisplayVersion)"
    Write-Host "  当前 node.exe  : $realVer"

    if ($realVer -eq $targetVer -and $regKey.DisplayVersion -eq $targetVer) {
        Write-Host "  (注册表与实际已一致，无需重装)" -ForegroundColor DarkGray
        return
    }

    # --- 下载 ---
    if (-not (Test-Path $msiPath)) {
        Write-Host "`n  下载 $msiUrl"
        $ProgressPreference = 'SilentlyContinue'
        try {
            Invoke-WebRequest -Uri $msiUrl -OutFile $msiPath -UseBasicParsing
        } catch {
            Write-Host "  [X] 下载失败：$($_.Exception.Message)" -ForegroundColor Red
            Write-Host "      可手动下载后放到 $msiPath 再重跑本脚本。" -ForegroundColor Yellow
            return
        }
    }
    Write-Host "  MSI: $msiPath  ($([math]::Round((Get-Item $msiPath).Length/1MB,1)) MB)"

    # --- 关闭占用 node.exe 的进程 ---
    $busy = Get-Process node, npm, npx, pnpm, corepack, code, cursor -ErrorAction SilentlyContinue
    if ($busy) {
        Write-Host "  [!] 以下进程可能占用文件，建议先关闭：" -ForegroundColor Yellow
        $busy | Select-Object ProcessName, Id | ForEach-Object { "        $($_.ProcessName) (PID $($_.Id))" }
        $ans = Read-Host "  仍要继续? (y/N)"
        if ($ans -ne 'y') { Write-Host "  已跳过 Node 重装。"; return }
    }

    # --- 安装（保持原安装目录，MSI 主版本升级会自动移除旧产品） ---
    Write-Host "`n  执行 msiexec ..."
    $log = Join-Path $BackupDir "node-msi-install-$Stamp.log"
    $args = @(
        '/i', "`"$msiPath`"",
        "INSTALLDIR=`"$installDir`"",
        '/qb', '/norestart',
        '/l*v', "`"$log`""
    )
    $proc = Start-Process -FilePath 'msiexec.exe' -ArgumentList $args -Wait -PassThru
    Write-Host "  msiexec 退出码: $($proc.ExitCode)   (0 = 成功, 3010 = 成功但需重启)"
    Write-Host "  日志: $log"

    # --- 验证 ---
    Write-Host "`n  --- 验证 ---"
    $newReal = if (Test-Path $nodeExe) { (Get-Item $nodeExe).VersionInfo.ProductVersion } else { '(未找到)' }
    $newReg  = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
               Where-Object { $_.DisplayName -like 'Node.js*' }
    Write-Host "  注册表版本 : $($newReg.DisplayVersion)"
    Write-Host "  node.exe   : $newReal"
    if ($newReal -eq $targetVer -and $newReg.DisplayVersion -eq $targetVer) {
        Write-Host "  [OK] 注册表与实际版本已一致" -ForegroundColor Green
    } else {
        Write-Host "  [!] 版本仍不一致，请查看日志" -ForegroundColor Yellow
    }
    & $nodeExe --version 2>&1 | ForEach-Object { "  node --version -> $_" }
}

# ==================================================================
Assert-Admin
Repair-MachinePath
Repair-NodeRegistry
Write-Host "`n===== 全部完成 =====" -ForegroundColor Green
Write-Host "备份目录: $BackupDir"
Write-Host "提示: 新开的终端才会读到更新后的 PATH。"
