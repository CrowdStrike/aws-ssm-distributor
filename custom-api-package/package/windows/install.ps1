<#
.SYNOPSIS
    Installs CrowdStrike Falcon

    MIT License

    Copyright © 2022 CrowdStrike, Inc.
    
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    #>
[CmdletBinding()]
param()

#########
# Setup #
#########

Write-Output 'Installing Falcon Sensor...'
    
$ErrorActionPreference = "Stop"
    
function Convert-EncodeQueryParameter {
    param (
        [Parameter(Mandatory = $true)]
        [string]$QueryParameter
    )
        
    return $QueryParameter.Replace("+", "%2b").Replace("'", "%27").Replace(":", "%3a").Replace(" ", "%20")
}
    
$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
    
if ($agentService) {
    Write-Output 'Falcon Sensor already installed... if you want to update or downgrade, please use Sensor Update Policies in the CrowdStrike console. Please see: https://falcon.crowdstrike.com/documentation/66/sensor-update-policies for more information.'
    Exit 0
}

if (-not $env:SSM_CS_CCID) {
    throw "Missing required parameter $($env:SSM_CS_CCID). If the required parameter was passed to the package, ensure the target instance has a ssm agent version of 2.3.1550.0 or greater installed."
}

$baseFilter = "os:'Windows'+platform:'windows'"

if ($env:SSM_CS_WINDOWS_VERSION) {
    $sensorFilter = Convert-EncodeQueryParameter -QueryParameter ($baseFilter + "+version:'${env:SSM_CS_WINDOWS_VERSION}'")
    $queryString = "limit=1&filter=${sensorFilter}"
    Write-Output "Version specified, grabbing the exact version: ${env:SSM_CS_WINDOWS_VERSION}. Query string: ${queryString}"
}
else {
    # If no version is specified, we will grab the n-1 version that matches the base filter
    $sensorFilter = Convert-EncodeQueryParameter -QueryParameter $baseFilter
    $queryString = "limit=1&offset=1&sort=version&filter=${sensorFilter}"
    Write-Output "No version specified, grabbing the n-1 version that matches the base filter. Query string: ${queryString}"
}

$headers = @{
    'Authorization' = "Bearer ${env:SSM_CS_AUTH_TOKEN}"
    'User-Agent'    = 'crowdstrike-custom-api-distributor-package/v2.0.0'
}  

$installArguments = @(
    , '/install'
    , '/quiet'
    , '/norestart'
    , "CID=${env:SSM_CS_CCID}"
    , 'ProvWaitTime=1200000'
)

$Space = ' '
if ($env:SSM_CS_WINDOWS_INSTALLPARAMS) {
    $installArguments += $env:SSM_CS_WINDOWS_INSTALLPARAMS.Split($Space)
}    

if ($env:SSM_CS_INSTALLTOKEN) {
    $installArguments += "ProvToken=${env:SSM_CS_INSTALLTOKEN}"
}

$proxy = ""

if ($installArguments -match "app_proxyname") {
    Write-Output "Proxy settings detected in arguments, using proxy settings to communicate with the CrowdStrike api"
    foreach ($arg in $installArguments) {
        $field = $arg.Split("=")
        
        if ($field[0] -eq "app_proxyname") {
            $proxy_host = $field[1].Replace("http://", "").Replace("https://", "")
            Write-Output "Proxy host ${proxy_host} found in arguments"
        }    

        if ($field[0] -eq "app_proxyport") {
            $proxy_port = $field[1]
            Write-Output "Proxy port ${proxy_port} found in arguments"
        }    
    }    

    if ($proxy_port -ne "") {
        $proxy = "http://${proxy_host}:${proxy_port}"
    }    
    else {
        $proxy = "http://${proxy_host}"
    }    

    $proxy = $proxy.Replace("'", "").Replace("`"", "")
    Write-Output "Using proxy: ${proxy} to communicate with the CrowdStrike Apis"
}    

###################
# Sensor Download #
###################

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$maxRetry = 15
$retryCount = 0
$retryDelaySeconds = 10

do {
    $uri = "https://${env:SSM_CS_HOST}/sensors/combined/installers/v1?${queryString}"
    Write-Output "Grabbing the Sha256 of the falcon sensor package, Calling $uri"
    try {
        if ($proxy -ne "") {
            $resp = Invoke-WebRequest -Method Get -Proxy $proxy -Uri $uri -Headers $headers -UseBasicParsing -ErrorAction Stop
        }    
        else {
            $resp = Invoke-WebRequest -Method Get -Uri $uri -Headers $headers -UseBasicParsing -ErrorAction Stop
        }    
    }    
    catch {
        $resp = $_.Exception.Response

        if ($null -eq $resp) {
            throw "Unexpected error: $($_.Exception.Message)"
        }    

        if ($resp.StatusCode -eq 429) {
            $retryCount++
            Write-Output "Rate limit exceeded, retrying in ${retryDelaySeconds} seconds... (retry ${retryCount} of ${maxRetry})"
            Start-Sleep -Seconds $retryDelaySeconds
        }    
    }    
} while ($retryCount -lt $maxRetry -and $resp.StatusCode -eq 429)    

if ($resp.StatusCode -eq 429) {
    throw "Rate limit exceeded, and max retries (${maxRetry}) reached."
}    

if ($resp.StatusCode -ne 200) {
    throw "Unexpected response code: $($resp.StatusCode) Response: $($resp.Content)"
}    
$content = ConvertFrom-Json -InputObject $resp.Content
# CHECK IF $content.resources IS EMPTY
# IF EMPTY, THROW ERROR
if ($content.resources.Count -eq 0) {
    throw "No sensor found for filter: ${queryString} Response: $($resp.Content)"
}
# Check if $resp.resources HAS MORE THAN 1 ELEMENT
# IF MORE THAN 1 ELEMENT, THROW ERROR
if ($content.resources.Count -gt 1) {
    throw "More than one sensor found for filter: ${queryString} Response: $($resp.Content)"
}    
# IF NOT EMPTY, CHECK IF $resp.resources[0].signed_url IS EMPTY/NULL or $resp.resources[0].name IS EMPTY/NULL
# IF EMPTY/NULL, THROW ERROR
if ($null -eq $content.resources[0].sha256 -or $null -eq $content.resources[0].name) {
    throw "Resources returned, but were missing the sha256 or name field. Please report this error. Response: $($resp.Content)"
}    

$installerName = $content.resources[0].name
$installerSha256 = $content.resources[0].sha256
$version = $content.resources[0].version

$ProgressPreference = 'SilentlyContinue'
$maxRetry = 15
$retryCount = 0
$retryDelaySeconds = 10
$installerPath = Join-Path -Path $PSScriptRoot -ChildPath $installerName

do {
    $uri = "https://${env:SSM_CS_HOST}/sensors/entities/download-installer/v1?id=$installerSha256"
    Write-Output "Downloading the package matching Sha256: $installerSha256. Calling $uri"
    try {
        if ($proxy -ne "") {
            $resp = Invoke-WebRequest -Method Get -Proxy $proxy -Uri $uri -Headers $headers -UseBasicParsing -OutFile $installerPath -ErrorAction Stop
        }    
        else {
            $resp = Invoke-WebRequest -Method Get -Uri $uri -Headers $headers -UseBasicParsing -OutFile $installerPath -ErrorAction Stop
        }    
    }    
    catch {
        $resp = $_.Exception.Response

        if ($null -eq $resp) {
            throw "Unexpected error: $($_.Exception.Message)"
        }    

        if ($resp.StatusCode -eq 429) {
            $retryCount++
            Write-Output "Rate limit exceeded, retrying in ${retryDelaySeconds} seconds... (retry ${retryCount} of ${maxRetry})"
            Start-Sleep -Seconds $retryDelaySeconds
        }    
    }    
} while ($retryCount -lt $maxRetry -and $resp.StatusCode -eq 429)    

if ($resp.StatusCode -eq 429) {
    throw "Rate limit exceeded, and max retries (${maxRetry}) reached."
}    

if (-not (Test-Path -Path $installerPath)) {
    throw "Failed to download the file. Error $(ConvertTo-Json $resp -Depth 10)"
} 

###########
# Install #
###########

Write-Host "Installer downloaded to: $installerPath"
Write-Output "Running installer for sensor version: ${version} with arguments: $installArguments"
$installerProcess = Start-Process -FilePath $installerPath -ArgumentList $installArguments -PassThru -Wait

if ($installerProcess.ExitCode -ne 0) {
    throw "Installer returned exit code $($installerProcess.ExitCode)"
}

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

Write-Output "Falcon Sensor version ${version} installed successfully."