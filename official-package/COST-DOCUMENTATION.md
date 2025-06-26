# Cost Documentation for AWS Systems Manager State Manager Associations

> ![IMPORTANT]
> The cost estimates provided in this document are based on AWS pricing as of June 26, 2025, and are intended as examples only. Actual costs may vary based on your specific usage patterns, and any changes to AWS pricing. For the most current pricing information, refer to the [AWS Systems Manager Pricing](https://aws.amazon.com/systems-manager/pricing/) page.

This document outlines the cost considerations when using AWS Systems Manager State Manager associations to deploy the CrowdStrike Falcon Sensor across your AWS environment.

## Overview

This documentation covers version 3 of the `CrowdStrike-FalconSensorDeploy` automation document, which contains 4 steps total compared to 7 steps in version 2.

AWS Systems Manager State Manager itself does not incur additional charges. However, when using the `CrowdStrike-FalconSensorDeploy` automation document with State Manager associations, there are cost implications related to the automation steps executed.

## Cost Components

### State Manager

- **Base Usage**: No additional charges for AWS Systems Manager State Manager itself.
- **Service Limits**: Standard [AWS service limits](https://docs.aws.amazon.com/general/latest/gr/aws_service_limits#limits_ssm) apply.

### Automation Steps

When the State Manager association runs the `CrowdStrike-FalconSensorDeploy` automation document, costs are incurred based on the number and type of automation steps executed:

1. **Basic Steps**:
   - Free tier: 100,000 steps per month
   - Beyond free tier: $0.002 per step

2. **`aws:executeScript` Steps**:
   - Free tier: 5,000 seconds of execution time per month
   - Beyond free tier: $0.00003 per second

### Automation Document Structure

The `CrowdStrike-FalconSensorDeploy` automation document (version 3) contains 4 total steps:
- 2 standard automation steps
- 2 `aws:executeScript` steps

## Cost Calculation Example

For a deployment with:
- 500 instances
- Association scheduled to run daily (30 executions per month)
- 4 steps per execution (2 standard steps + 2 `aws:executeScript` steps)

**Monthly step count**: 500 instances × 30 executions × 4 steps = 60,000 steps  
**Cost for steps**: Covered under free tier (100,000 steps)

**`aws:executeScript` Execution Time**:
- Average execution time: 3 seconds per `aws:executeScript` step
- Monthly execution seconds: 500 instances × 30 executions × 2 `aws:executeScript` steps × 3 seconds = 90,000 seconds
- Billable seconds: 90,000 - 5,000 = 85,000 seconds
- **Cost for execution time**: 85,000 seconds × $0.00003 = $2.55 per month

**Total monthly cost**: $0 (steps) + $2.55 (execution time) = $2.55

For a larger deployment or more frequent executions:  
**Example**: 1,000 instances × 30 executions × 4 steps = 120,000 steps  
**Billable steps**: 120,000 - 100,000 = 20,000 steps  
**Cost for steps**: 20,000 steps × $0.002 = $40.00 per month

**`aws:executeScript` Execution Time**:
- Average execution time: 3 seconds per `aws:executeScript` step
- Monthly execution seconds: 1,000 instances × 30 executions × 2 `aws:executeScript` steps × 3 seconds = 180,000 seconds
- Billable seconds: 180,000 - 5,000 = 175,000 seconds
- **Cost for execution time**: 175,000 seconds × $0.00003 = $5.25 per month

**Total monthly cost**: $40.00 (steps) + $5.25 (execution time) = $45.25

## Additional Cost Considerations

1. **Secret Storage**:
   - **AWS Secrets Manager**: Incurs a cost per secret and per 10,000 API calls
   - **AWS Parameter Store**: Standard tier parameters are free, while advanced parameters incur a cost

2. **Execution Frequency**:
   - More frequent association schedules increase the number of automation steps executed
   
## Best Practices for Cost Optimization

1. **Use the Default Version**:
   - Always use the default version of the `CrowdStrike-FalconSensorDeploy` automation document
   - The default version will always be the most stable and cost-effective implementation
   - Versions 1 and 2 will be disabled when AWS removes support for Python 3.7

2. **Optimize Schedule Frequency**:
   - Consider if hourly execution is necessary or if a less frequent schedule could be used

3. **Parameter Store vs Secrets Manager**:
   - If cost is a primary concern, use Parameter Store instead of Secrets Manager for storing API credentials
