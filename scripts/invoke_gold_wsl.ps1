[CmdletBinding()]
param(
    [ValidateSet('Clone', 'Sync', 'Verify', 'StartEpisode', 'SelectBootstrap', 'Bootstrap', 'Fast', 'CompleteAudit')]
    [string]$Action = 'Fast',
    [string]$Distribution = 'Ubuntu-24.04',
    [string]$LinuxUser = 'luish',
    [string]$LinuxRepo = '/home/luish/src/Marketing_Swipe_File',
    [string]$LinuxDataRoot,
    [string]$LinuxJobRoot,
    [string]$ParityReceipt = '/home/luish/.cache/msf/runtime-parity/latest.json',
    [string]$RequestPath,
    [string]$RepositoryUrl,
    [string]$InvocationReceipt,
    [switch]$Initialize,
    [switch]$DryRun,
    [string[]]$CommandArguments
)

$ErrorActionPreference = 'Stop'
$EpicStarted = [DateTimeOffset]::UtcNow
$CommandArguments = @($CommandArguments | Where-Object { $null -ne $_ })
if ($Distribution.StartsWith('-') -or $LinuxUser.StartsWith('-') -or $LinuxRepo.StartsWith('-')) {
    throw 'Linux runtime arguments must be passed as an explicit array through -CommandArguments.'
}
$WindowsRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$WslHostIdentity = ((& whoami 2>$null | Select-Object -First 1) -as [string]).Trim()
if (-not $WslHostIdentity) { $WslHostIdentity = "$env:USERDOMAIN\\$env:USERNAME" }
$WslHostPreflight = [ordered]@{
    windows_identity = $WslHostIdentity
    distribution = $Distribution
    validation_route = 'explicit_contract_no_distro_enumeration'
    status = 'deferred_to_direct_invocation'
}
$Drive = $WindowsRepo.Substring(0, 1).ToLowerInvariant()
$Tail = $WindowsRepo.Substring(2).Replace('\', '/')
$MountedRepo = "/mnt/$Drive$Tail"
$MountedSync = "$MountedRepo/scripts/sync_wsl_runtime.py"
$MountedManifest = "$MountedRepo/scripts/gold_runtime_sync_manifest.json"
$LinuxPython = "$LinuxRepo/.venv/bin/python"
$LinuxHome = "/home/$LinuxUser"
if (-not $LinuxDataRoot) { $LinuxDataRoot = "$LinuxHome/msf-data/Marketing_Swipe_File" }
if (-not $LinuxJobRoot) { $LinuxJobRoot = "$LinuxHome/.cache/msf/jobs" }
$StartJobDir = "$LinuxJobRoot/start-$($EpicStarted.UtcDateTime.ToString('yyyyMMddTHHmmssfffZ'))"
$LinuxEnvironment = @(
    '/usr/bin/env',
    "HOME=$LinuxHome",
    'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
    'LANG=C.UTF-8',
    'LC_ALL=C.UTF-8',
    'MSF_GOLD_RUNTIME=wsl_linux',
    'PYTHONNOUSERSITE=1'
)
if (-not $RepositoryUrl) {
    $RepositoryUrl = (& git -C $WindowsRepo remote get-url origin 2>$null)
}
$CloneArguments = @(
    '-d', $Distribution, '-u', $LinuxUser, '--exec'
) + $LinuxEnvironment + @('/usr/bin/git', 'clone', '--origin', 'origin', $RepositoryUrl, $LinuxRepo)
$SyncArguments = @(
    '-d', $Distribution, '-u', $LinuxUser, '--exec'
) + $LinuxEnvironment + @(
    '/usr/bin/python3', $MountedSync,
    '--source-root', $MountedRepo,
    '--destination-root', $LinuxRepo,
    '--manifest', $MountedManifest,
    '--receipt', $ParityReceipt
)
if ($Initialize) { $SyncArguments += '--initialize' }
if ($Action -eq 'Verify') { $SyncArguments += '--check' }
if (-not $Initialize -and $Action -ne 'Verify') { $SyncArguments += '--reuse-valid' }

$Module = if ($Action -eq 'CompleteAudit') { 'scripts.complete_gold_episode' } else { 'scripts.run_gold_episode_fast' }
$RuntimeArguments = @(
    '-d', $Distribution, '-u', $LinuxUser,
    '--cd', $LinuxRepo, '--exec'
) + $LinuxEnvironment + @(
    $LinuxPython, '-m', $Module,
    '--runtime-parity-receipt', $ParityReceipt,
    '--runtime-manifest', "$LinuxRepo/scripts/gold_runtime_sync_manifest.json"
) + $CommandArguments

if ($Action -eq 'SelectBootstrap') {
    $RuntimeArguments = @(
        '-d', $Distribution, '-u', $LinuxUser,
        '--cd', $LinuxRepo, '--exec'
    ) + $LinuxEnvironment + @(
        $LinuxPython, '-m', 'scripts.run_gold_episode_fast',
        '--runtime-parity-receipt', $ParityReceipt,
        '--runtime-manifest', "$LinuxRepo/scripts/gold_runtime_sync_manifest.json",
        '--select-next',
        '--priority-queue', "$LinuxRepo/docs/coordination/gold-episode-priority-queue.json",
        '--epic-started-at', $EpicStarted.ToString('o')
    ) + $CommandArguments
}

$StartArguments = @(
    '-d', $Distribution, '-u', $LinuxUser, '--exec'
) + $LinuxEnvironment + @(
    '/usr/bin/python3', $MountedSync,
    '--source-root', $MountedRepo,
    '--destination-root', $LinuxRepo,
    '--manifest', $MountedManifest,
    '--receipt', $ParityReceipt,
    '--reuse-valid',
    '--exec-after',
    $LinuxPython, '-m', 'scripts.run_gold_episode_fast',
    '--runtime-parity-receipt', $ParityReceipt,
    '--runtime-manifest', "$LinuxRepo/scripts/gold_runtime_sync_manifest.json",
    '--start-episode',
    '--data-root', $LinuxDataRoot,
    '--job-dir', $StartJobDir,
    '--priority-queue', "$LinuxRepo/docs/coordination/gold-episode-priority-queue.json",
    '--epic-started-at', $EpicStarted.ToString('o')
) + $CommandArguments

if ($Action -eq 'Bootstrap') {
    if (-not $RequestPath) { throw '-RequestPath is required for Bootstrap.' }
    $RequestFull = [IO.Path]::GetFullPath($RequestPath)
    $RequestDrive = $RequestFull.Substring(0, 1).ToLowerInvariant()
    $RequestTail = $RequestFull.Substring(2).Replace('\', '/')
    $MountedRequest = "/mnt/$RequestDrive$RequestTail"
    $RuntimeArguments = @(
        '-d', $Distribution, '-u', $LinuxUser,
        '--cd', $LinuxRepo, '--exec'
    ) + $LinuxEnvironment + @(
        $LinuxPython, '-m', 'scripts.run_gold_episode_fast',
        '--runtime-parity-receipt', $ParityReceipt,
        '--runtime-manifest', "$LinuxRepo/scripts/gold_runtime_sync_manifest.json",
        '--bootstrap-request', $MountedRequest
    )
}

if ($DryRun) {
    Write-Output (@{ clone = $CloneArguments; sync = $SyncArguments; start = $StartArguments; runtime = $RuntimeArguments } | ConvertTo-Json -Depth 5)
    exit 0
}

$Started = $EpicStarted
$SyncExit = 0
$RuntimeExit = $null
$CloneExit = $null
$FailureStage = $null
$UsePinnedRuntime = $Action -in @('Fast', 'CompleteAudit')
try {
    if ($Action -eq 'Clone') {
        & wsl.exe @CloneArguments
        $CloneExit = $LASTEXITCODE
        if ($CloneExit -ne 0) { $FailureStage = 'clone'; exit $CloneExit }
        $SyncArguments += '--initialize'
    }
    if ($Action -eq 'StartEpisode') {
        & wsl.exe @StartArguments
        $RuntimeExit = $LASTEXITCODE
        $SyncExit = if ($RuntimeExit -eq 0) { 0 } else { $null }
        if ($RuntimeExit -ne 0) { $FailureStage = 'certified_start' }
        exit $RuntimeExit
    }
    if (-not $UsePinnedRuntime) {
        & wsl.exe @SyncArguments
        $SyncExit = $LASTEXITCODE
        if ($SyncExit -ne 0) { $FailureStage = 'runtime_sync' }
        if ($SyncExit -ne 0 -or $Action -in @('Clone', 'Sync', 'Verify')) {
            exit $SyncExit
        }
    }
    & wsl.exe @RuntimeArguments
    $RuntimeExit = $LASTEXITCODE
    if ($RuntimeExit -ne 0) { $FailureStage = 'wsl_runtime' }
    exit $RuntimeExit
}
finally {
    if ($InvocationReceipt) {
        $Ended = [DateTimeOffset]::UtcNow
        $Receipt = @{
            schema_version = '1.0.0'
            action = $Action
            started_at = $Started.ToString('o')
            ended_at = $Ended.ToString('o')
            elapsed_ms = [Math]::Round(($Ended - $Started).TotalMilliseconds, 2)
            sync_argv = $SyncArguments
            start_argv = $StartArguments
            runtime_argv = $RuntimeArguments
            sync_exit_code = $SyncExit
            runtime_exit_code = $RuntimeExit
            clone_exit_code = $CloneExit
            failure_stage = $FailureStage
            windows_fallback_used = $false
            environment_contract = @{
                distribution = $Distribution
                linux_user = $LinuxUser
                linux_repo = $LinuxRepo
                discovery_route = 'current_windows_identity_wsl_registry_preflight'
                host_preflight = $WslHostPreflight
                certified = ($SyncExit -eq 0 -and ($RuntimeExit -eq 0 -or $Action -in @('Clone', 'Sync', 'Verify')))
            }
        }
        $ReceiptPath = [IO.Path]::GetFullPath($InvocationReceipt)
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($ReceiptPath)) | Out-Null
        [IO.File]::WriteAllText($ReceiptPath, ($Receipt | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
    }
}
