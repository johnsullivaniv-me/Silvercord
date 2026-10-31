<#
.SYNOPSIS
  Links this repo's addon folder into your WoW AddOns directory (dev install).

.DESCRIPTION
  Creates a directory junction:
      <WoW>\<flavor>\Interface\AddOns\Silvercord  ->  <repo>\addon\Silvercord
  so edits in the repo are live after a /reload. Junctions need no admin
  rights and no Developer Mode.

  The WoW: Forever flavor folder name (e.g. _classic_beta_ in the beta) isn't
  known for launch, so the script lists the _*_ folders it finds and asks,
  unless you pass -Flavor.

.PARAMETER WowPath
  WoW install root, e.g. "C:\Program Files (x86)\World of Warcraft".
  Auto-detected from the registry / common locations if omitted.

.PARAMETER Flavor
  Flavor folder name, e.g. _forever_ or _classic_beta_.

.PARAMETER Force
  If a real (non-link) Silvercord folder already exists, rename it to a
  timestamped backup and link anyway.

.PARAMETER Uninstall
  Remove the junction (only the link; never the repo's files).

.EXAMPLE
  .\scripts\install-dev.ps1
.EXAMPLE
  .\scripts\install-dev.ps1 -WowPath "D:\Games\World of Warcraft" -Flavor _forever_
.EXAMPLE
  .\scripts\install-dev.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$WowPath,
    [string]$Flavor,
    [switch]$Force,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

$Source = (Resolve-Path (Join-Path $PSScriptRoot '..\addon\Silvercord')).Path
if (-not (Test-Path (Join-Path $Source 'Silvercord.toc'))) {
    throw "Can't find addon\Silvercord\Silvercord.toc next to this script. Run it from the repo."
}

function Find-WowRoot {
    $candidates = @()
    $keys = @(
        'HKLM:\SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft',
        'HKLM:\SOFTWARE\Blizzard Entertainment\World of Warcraft'
    )
    foreach ($k in $keys) {
        try {
            $p = (Get-ItemProperty -Path $k -Name InstallPath -ErrorAction Stop).InstallPath
            if ($p) {
                $p = $p.TrimEnd('\')
                # InstallPath often points at a flavor folder like ...\_retail_
                if ((Split-Path $p -Leaf) -match '^_.+_$') { $p = Split-Path $p -Parent }
                $candidates += $p
            }
        } catch { }
    }
    $candidates += @(
        "${env:ProgramFiles(x86)}\World of Warcraft",
        "$env:ProgramFiles\World of Warcraft",
        'C:\Games\World of Warcraft',
        'D:\World of Warcraft',
        'D:\Games\World of Warcraft',
        'E:\World of Warcraft'
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c -PathType Container) -and
            (Get-ChildItem $c -Directory -Filter '_*_' -ErrorAction SilentlyContinue)) {
            return (Resolve-Path $c).Path
        }
    }
    return $null
}

if (-not $WowPath) { $WowPath = Find-WowRoot }
if (-not $WowPath -or -not (Test-Path $WowPath -PathType Container)) {
    throw "Couldn't find World of Warcraft. Pass -WowPath 'X:\path\to\World of Warcraft'."
}
Write-Host "WoW root: $WowPath"

$flavors = @(Get-ChildItem $WowPath -Directory -Filter '_*_' | Select-Object -ExpandProperty Name)
if ($Flavor) {
    if ($flavors -notcontains $Flavor) {
        throw "No '$Flavor' folder under $WowPath. Found: $($flavors -join ', ')"
    }
} elseif ($flavors.Count -eq 1) {
    $Flavor = $flavors[0]
} elseif ($flavors.Count -eq 0) {
    throw "No game flavor folders (like _retail_ or _classic_era_) under $WowPath. Has the game been installed and launched once?"
} else {
    Write-Host "Several game folders found:"
    for ($i = 0; $i -lt $flavors.Count; $i++) { Write-Host ("  [{0}] {1}" -f ($i + 1), $flavors[$i]) }
    $pick = Read-Host "Install into which one? (number)"
    $n = 0
    if (-not [int]::TryParse($pick, [ref]$n) -or $n -lt 1 -or $n -gt $flavors.Count) {
        throw "Not a valid choice: '$pick'"
    }
    $Flavor = $flavors[$n - 1]
}

$AddOns = Join-Path (Join-Path $WowPath $Flavor) 'Interface\AddOns'
$Target = Join-Path $AddOns 'Silvercord'

function Get-LinkInfo([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $item = Get-Item -LiteralPath $Path -Force
    $isLink = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    $linkTarget = $null
    if ($isLink -and $item.PSObject.Properties['Target']) { $linkTarget = @($item.Target)[0] }
    return [pscustomobject]@{ IsLink = $isLink; Target = $linkTarget }
}

function Remove-Link([string]$Path) {
    # Directory.Delete on a junction removes only the link, never the files
    # it points at. (Remove-Item -Recurse on a junction can delete contents
    # in older PowerShell versions, so it is deliberately not used here.)
    [IO.Directory]::Delete($Path, $false)
}

$existing = Get-LinkInfo $Target

if ($Uninstall) {
    if (-not $existing) { Write-Host "Nothing to remove at $Target."; return }
    if (-not $existing.IsLink) {
        throw "$Target is a real folder, not a link. Not touching it."
    }
    Remove-Link $Target
    Write-Host "Removed link $Target. (Your repo files are untouched.)"
    return
}

if ($existing) {
    if ($existing.IsLink) {
        if ($existing.Target -and ((Resolve-Path $existing.Target -ErrorAction SilentlyContinue).Path -eq $Source)) {
            Write-Host "Already linked: $Target -> $Source"
            return
        }
        Write-Host "Replacing existing link ($($existing.Target))."
        Remove-Link $Target
    } elseif ($Force) {
        $backup = "$Target.backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
        Rename-Item -LiteralPath $Target -NewName (Split-Path $backup -Leaf)
        Write-Host "Moved existing folder to $backup"
    } else {
        throw "$Target already exists and is a real folder (an installed copy?). Re-run with -Force to back it up and link instead."
    }
}

if (-not (Test-Path $AddOns)) { New-Item -ItemType Directory -Path $AddOns -Force | Out-Null }
New-Item -ItemType Junction -Path $Target -Target $Source | Out-Null

# Verify: the TOC must be visible through the link.
if (-not (Test-Path (Join-Path $Target 'Silvercord.toc'))) {
    throw "Link creation reported success but $Target doesn't show the addon files. Is the repo on a network/WSL drive? Junctions need a local NTFS path; copy the folder instead."
}

Write-Host ""
Write-Host "Linked $Target"
Write-Host "    -> $Source"
Write-Host ""
Write-Host "Next: start WoW, open AddOns on the character screen, and make sure Silvercord is enabled."
Write-Host "If it shows as 'out of date', check the interface number in-game with"
Write-Host "    /dump select(4, GetBuildInfo())"
Write-Host "and update '## Interface:' in addon\Silvercord\Silvercord.toc."
