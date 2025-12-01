![CrowdStrike Logo (Light)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-light-mode.png#gh-light-mode-only)
![CrowdStrike Logo (Dark)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-dark-mode.png#gh-dark-mode-only)

# AWS Systems Manager Integrations

This repository contains the documentation and source code to deploy the CrowdStrike Falcon Sensor using AWS Systems Manager.

## Demo

[![Demo of the AWS SSM Distributor Package](https://play.vidyard.com/xGheoUHy1QhhTcrQvgz2Bd.jpg)](https://vid.crowdstrike.com/watch/xGheoUHy1QhhTcrQvgz2Bd)

## Overview

| Integration | Description | Use Case | API Keys Required |
| --- | --- | --- | --- |
| [Official AWS Distributor Package](./official-package/README.md) | Install the falcon sensor on instances across your aws account using AWS SSM | Automatically install the sensor on Windows and Linux instances. | Yes |
| [Custom Distributor Package using agent binaries](./custom-binary-package/README.md) | Install the falcon sensor on instances across your aws account using AWS SSM | Automatically install the sensor on Windows and Linux instances using a self managed package that does not require api access. | No |
