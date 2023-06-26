
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
 
## [Unreleased] - yyyy-mm-dd
 
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
- Instead of releasing a distributor package per sensor version, we now version the package by changes to the script. Current version is `v1.0.0`
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