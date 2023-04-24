# AWS Systems Manager Integrations

This repository contains the documentation and source code to deploy the CrowdStrike Falcon Sensor using AWS Systems Manager.

## Overview

| Integration | Description | Use Case | API Keys Required |
| --- | --- | --- | --- |
| [Official AWS Distributor Package](./official-package/README.md) | Install the falcon sensor on instances across your aws account using AWS SSM | Automatically install the sensor on Windows and Linux instances. | Yes |
| [Custom Distributor Package using API](./custom-api-package/README.md) | Install the falcon sensor on instances across your aws account using AWS SSM | Automatically install the sensor on Windows and Linux instances using a self managed package. | No |