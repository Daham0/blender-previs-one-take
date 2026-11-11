# Blender 便携版安装脚本（不写注册表、不占 C 盘、可整目录删除）
# 用法：
#   powershell -ExecutionPolicy Bypass -File install_blender.ps1
#   powershell -ExecutionPolicy Bypass -File install_blender.ps1 -TargetDir "D:\Agent\Marvis" -Version "4.5.9"
#   powershell -ExecutionPolicy Bypass -File install_blender.ps1 -DryRun
# 说明：官方站点在部分网络环境返回 403，脚本会自动切换国内镜像（阿里云/清华）。

param(
  [string]$TargetDir = "D:\Agent\Marvis",
  [string]$Version = "",
  [ValidateSet("auto","official","aliyun","tuna")][string]$Mirror = "auto",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$mirrors = @{
  official = "https://download.blender.org/release"
  aliyun   = "https://mirrors.aliyun.com/blender/release"
  tuna     = "https://mirrors.tuna.tsinghua.edu.cn/blender/release"
}
$order = switch ($Mirror) {
  "official" { @("official") }
  "aliyun"   { @("aliyun") }
  "tuna"     { @("tuna") }
  default    { @("official","aliyun","tuna") }
}

$series = "Blender4.5"   # 需要 5.x 时改这里或传 -Version 后手工指定

function Get-LatestVersion($baseUrl, $series) {
  $url = "$baseUrl/$series/"
  $html = (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30).Content
  $m = [regex]::Matches($html, 'blender-(\d+\.\d+\.\d+)-windows-x64\.zip')
  if ($m.Count -eq 0) { return $null }
  $vers = $m | ForEach-Object { $_.Groups[1].Value } | Sort-Object { [version]$_ }
  return $vers[-1]
}

$chosen = $null
foreach ($m in $order) {
  $b = $mirrors[$m]
  try {
    $v = if ($Version) { $Version } else { Get-LatestVersion $b $series }
    if (-not $v) { continue }
    $url = "$b/$series/blender-$v-windows-x64.zip"
    $probe = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 30
    if ($probe.StatusCode -eq 200) {
      $chosen = [pscustomobject]@{ mirror = $m; version = $v; url = $url; size = $probe.Headers["Content-Length"] }
      break
    }
  } catch {
    Write-Host "镜像 $m 不可用：$($_.Exception.Message)"
  }
}
if (-not $chosen) { throw "所有镜像均不可用。请手动下载 Blender 便携版 zip 并解压到 $TargetDir，然后设置环境变量 BLENDER_PATH 指向 blender.exe" }

$mb = if ($chosen.size) { [math]::Round([int64]$chosen.size / 1MB, 1) } else { "?" }
Write-Host "[计划] 镜像=$($chosen.mirror) 版本=$($chosen.version) 大小约 $mb MB"
Write-Host "       URL=$($chosen.url)"
Write-Host "       安装到=$TargetDir（便携模式，不写注册表）"
if ($DryRun) { Write-Host "[DryRun] 未执行下载"; exit 0 }

if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
$zip = Join-Path $TargetDir ("blender-" + $chosen.version + "-windows-x64.zip")

if (-not (Test-Path $zip)) {
  Write-Host "[1/4] 下载中（约 $mb MB，请勿关闭）..."
  Invoke-WebRequest -Uri $chosen.url -OutFile $zip -UseBasicParsing -TimeoutSec 1800
} else { Write-Host "[1/4] 复用已下载的 $zip" }

Write-Host "[2/4] 解压..."
Expand-Archive -Path $zip -DestinationPath $TargetDir -Force

$exe = Get-ChildItem -Path $TargetDir -Recurse -Filter "blender.exe" |
        Where-Object { $_.FullName -notmatch "\\Blender Foundation\\" } |
        Select-Object -First 1
if (-not $exe) { throw "解压后未找到 blender.exe，请检查压缩包结构" }

$portable = Join-Path $exe.DirectoryName "portable"
if (-not (Test-Path $portable)) { New-Item -ItemType Directory -Path $portable -Force | Out-Null }

Write-Host "[3/4] 写入环境变量 BLENDER_PATH"
[Environment]::SetEnvironmentVariable("BLENDER_PATH", $exe.FullName, "User")
$env:BLENDER_PATH = $exe.FullName

Write-Host "[4/4] 自检（后台启动一次）"
& $exe.FullName -b --python-expr "import bpy;print('VER:'+bpy.app.version_string)" | Select-String "VER:"

Write-Host ""
Write-Host "完成。blender.exe = $($exe.FullName)"
Write-Host "删除方式：直接删除 $TargetDir 下对应版本目录，并清除用户环境变量 BLENDER_PATH。"
