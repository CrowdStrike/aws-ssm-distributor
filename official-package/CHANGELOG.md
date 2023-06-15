
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
 
## [Unreleased] - yyyy-mm-dd
 
### Added
- Secrets Manager as a option for storing the required secrets (Client ID, Client Secret, and Cloud).
- `User-Agent` header to track usage.
 
### Changed

- Backoff logic added to automation document to handle 429 errors.
- Reduced automation document steps to increase execution speed.
- Backoff logic added to install scripts to handle 429 errors.
- Prevent api calls if sensor is already installed.
- 3xx redirects now use the `Location` header to determine the correct url instead of throwing an error.
- Rewrote automation document to handle common api errors
 
### Fixed

- CFT for required role missing permissions.

### Misc

- Added FAQ
- Added table for supported regions
- Added table for supported operating systems
- Added automation statuses definitions
- Updated automation document params table
 
## [v0.0.1] - 2023-04-23
  
### Added

- Initial release