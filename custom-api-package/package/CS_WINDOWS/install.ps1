[CmdletBinding()]
param()

Write-Output 'Installing Falcon Sensor...'

# Configures the TLS version to use for secure connections
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 

$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue

if ($agentService) {
  Write-Output 'CSAgent service already installed...'
  Exit 0
}

# If the SSM_HOST environment variable does not begin with 'https://', prepends it
if (!$env:SSM_HOST.StartsWith('https://')) {
  $env:SSM_HOST = 'https://' + $env:SSM_HOST
}

# Removes any trailing slashes from the SSM_HOST environment variable
if ($env:SSM_HOST.EndsWith('/')) {
  $env:SSM_HOST = $env:SSM_HOST.TrimEnd('/')
}

$headers =  @{
  'Authorization' = "Bearer ${env:SSM_AUTH_TOKEN}"
  'User-Agent' = 'crowdstrike-custom-distributor-package/v1.0.0'
}

# Sends a GET request to the CrowdStrike API to retrieve the latest installer information
$installerQueryResp = Invoke-RestMethod -Method Get -Uri "${env:SSM_HOST}/sensors/combined/installers/v1?offset=1&limit=1&sort=version&filter=platform:'windows'" -Headers $headers -ErrorAction Stop

# If the API response does not contain a valid sha256 value, throws an exception
if (!$installerQueryResp.resources[0].sha256) {
  throw 'API response does not contain a valid sha256 value'
}

# Extracts the sha256 hash and name of the installer from the API response
$installerSha256 = $installerQueryResp.resources[0].sha256
$installerName = $installerQueryResp.resources[0].name

# Constructs the URL to download the installer
$downloadUrl = "${env:SSM_HOST}/sensors/entities/download-installer/v1?id=$installerSha256"

# Constructs the full path to save the installer to
$installerPath = Join-Path -Path $PSScriptRoot -ChildPath $installerName

# Downloads the installer and saves it to the specified path
$downloadSensorResp = Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -Headers $headers -ErrorAction Stop

# If the installer fails to download, throws an exception
if (-not (Test-Path -Path $installerPath)) {
  throw "Failed to download the file. Error $(ConvertTo-Json $downloadSensorResp -Depth 10)"
}

# If the SSM_CID environment variable is not set, throws an exception
if (-not $env:SSM_CID) {
  throw "Missing required param $($env:SSM_CID). Ensure the target instance is running the latest SSM agent version"
}

Write-Host "Installer downloaded to: $installerPath"

# Constructs the arguments to pass to the installer executable
$installArguments = @(
  , '/install'
  , '/quiet'
  , '/norestart'
  , "CID=${env:SSM_CID}"
  , 'ProvWaitTime=1200000'
)

# If the SSM_INSTALLTOKEN environment variable is set, include it in the installer arguments
if ($env:SSM_INSTALLTOKEN) {
  $installArguments += "ProvToken=${env:SSM_INSTALLTOKEN}"
}

# If the WIN_INSTALLERPARAMS environment is set, include it in the installer arguments
$space = ' '
if ($env:SSM_WIN_INSTALLPARAMS) {
  $installArguments += $env:SSM_WIN_INSTALLPARAMS.Split($space)
}

Write-Output 'Running installer...'
$installerProcess = Start-Process -FilePath $installerPath -ArgumentList $installArguments -PassThru -Wait

# If the installer process returns a non-zero exit code, throws an exception
if ($installerProcess.ExitCode -ne 0) {
  throw "Installer returned exit code $($installerProcess.ExitCode)"
}

# Verify teh CSAgent service is running
$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if (-not $agentService) {
  throw 'Installer completed, but CSAgent service is missing...'
}
elseif ($agentService.Status -eq 'Running') {
  Write-Output 'CSAgent service running...'
}
else {
  throw 'Installer completed, but CSAgent service is not running...'
}

Write-Output 'Successfully completed installation...'
