<#
.SYNOPSIS
    Installs CrowdStrike Falcon
#>
[CmdletBinding()]
param()
Write-Output 'Installing Falcon Sensor...'

$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue

if ($agentService) {
    Write-Output 'CSAgent service already installed...'
    Exit 0
}

$InstallerName = 'WindowsSensor.exe'
$InstallerPath = Join-Path -Path $PSScriptRoot -ChildPath $InstallerName

if (-not (Test-Path -Path $InstallerPath))
{
    throw "${InstallerName} not found."
}

if (-not $env:SSM_CID)
{
    throw 'Missing required param SSM_CID. Ensure the target instance is running the latest SSM agent version'
}

$InstallArguments = @(
    , '/install'
    , '/quiet'
    , '/norestart'
    , "CID=${env:SSM_CID}"
    , 'ProvWaitTime=180'
)

if ($env:SSM_INSTALLTOKEN)
{
    $InstallArguments += "ProvToken=${env:SSM_INSTALLTOKEN}"
}

$Space = ' '
if ($env:SSM_WIN_INSTALLPARAMS)
{
    $InstallArguments += $env:SSM_WIN_INSTALLPARAMS.Split($Space)
}

Write-Output 'Running installer...'
Write-Output $InstallArguments
$InstallerProcess = Start-Process -FilePath $InstallerPath -ArgumentList $InstallArguments -PassThru -Wait

if ($InstallerProcess.ExitCode -ne 0)
{
    throw "Installer returned exit code $($InstallerProcess.ExitCode)"
}

$AgentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if (-not $AgentService)
{
    throw 'Installer completed, but CSAgent service is missing...'
}
elseif ($AgentService.Status -eq 'Running')
{
    Write-Output 'CSAgent service running...'
}
else
{
    throw 'Installer completed, but CSAgent service is not running...'
}

Write-Output 'Successfully completed installation...'
