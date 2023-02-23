# AWS Systems Manager Integrations

This repository contains the documentation and source code to deploy the CrowdStrike Falcon Sensor using AWS Systems Manager.

## Overview

There are a few different ways to deploy the CrowdStrike Falcon Sensor using AWS Systems Manager. The following table outlines the different methods and their use cases.

| Method | Description | Use Case | API Keys Required |
| --- | --- | --- | --- |
| [Offical AWS Distributor Package](./deployment-guides/published-distributor-package.md) | This method uses the published third party distributor package in AWS. | This method prevents the need to build your own packages and publish documents to AWS. | Yes |