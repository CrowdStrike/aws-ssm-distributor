
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [v2.3.0] - 12-16-2024

### Added

- Support for RHEL 10 (x86_64, arm64)
- Support for Rocky Linux 10 (x86_64, arm64)
- Support for Oracle Linux 10 (x86_64, arm64)
- Support for AlmaLinux 10 (x86_64, arm64)
- Support for CentOS Stream 10 (x86_64)
- Support for Debian 13 (x86_64)
- Support for Oracle Linux 7 (arm64)
- Support for SLES 15 (arm64)

### Removed

- Support for CentOS 7
- Support for Oracle Linux 6

## [v2.2.0] - 06-23-2025

### Added

- Support for CentOS 9 (x86_64)
- Support for Oracle Enterprise Linux 9 (x86_64)

## [v2.0.0] - 12-02-2024

### Added

- Ubuntu 24.04 x86_64/arm64 support
- Two new automation level outputs for a general message and a error message.
- Per instance reporting on why they were skipped (Shutdown, Terminated, ConnectionLost, Unkown) with instructions on resolving the issue.
- Consolidated package `FalconSensor-CrowdStrike` for both windows and linux
- Reduced overall cost of using the `CrowdStrike-FalconSensorDeploy` automation document
- Updated retry logic to handle aws backoff requests

## [v1.1.0] - 07-28-2023

### Added

- Support for Amazon Linux 2023 (arm64 and x86_64)
- Support for Ubuntu 18/20/22 arm64
- Support for Debian 9/10/11 x86_64

### Fixed

- Fixed noninteractive warnings on debian based systems
 
## [v1.0.0] - 06-28-2023
 
### Added
- Secrets Manager as a option for storing the required secrets (Client ID, Client Secret, and Cloud).
- `User-Agent` header to track usage.
- Oauth tokens are revoked after the run is complete.
 
### Changed

- Backoff logic added to automation document to handle 429 errors.
- Reduced automation document steps to increase execution speed.
- Backoff logic added to install scripts to handle 429 errors.
- Prevent api calls if sensor is already installed.
- 3xx redirects now use the `Location` header to determine the correct url instead of throwing an error.
- Rewrote automation document to handle common api errors
- `FalconSensor-Linux` and `FalconSensor-Windows` can now be used for both operating systems. There is no difference between the two packages.
- Update linux/windows install scripts to install the n-1 version, but allow a specific version using `LinuxPackageVersion` or `WindowsPackageVersion`
- Instead of releasing a distributor package per sensor version, we now version the package by changes to the script.
- In-place update is the default install behavior. Sensor version upgrades and downgrades should be handled by Sensor Update Policies.
- IAM Role CloudFormation now includes permissions for secrets manager.
 
### Fixed

- CFT for required role missing permissions.
- The automation document now fails correctly when windows machines fail. Previously the status would show success.

### Misc

- Added FAQ
- Added table for supported regions
- Added table for supported operating systems
- Added automation statuses definitions
- Updated automation document params table
 
## [v0.0.1] - 2023-04-23
  
### Added

- Initial release
