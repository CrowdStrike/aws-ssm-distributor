# Troubleshooting

## Collecting logs from a Distributor package run

The Falcon sensor is installed by the `FalconSensor-CrowdStrike` Distributor
package. The `CrowdStrike-FalconSensorDeploy` automation document deploys it
through AWS's `AWS-ConfigureAWSPackage` run command, which executes the package
on each instance. AWS Systems Manager captures the install/uninstall output
from each run.

There are three ways to retrieve those logs:

- **[Using the AWS CLI](#method-1--using-the-aws-cli)** — pull the logs from
  your workstation without connecting to the instance.
- **[Using the AWS console](#method-2--using-the-aws-console)** — view the logs
  in the browser.
- **[On the instance](#method-3--on-the-instance)** — read the log files
  directly on the host.

The CLI and console methods work for runs within the last ~30 days. For older
runs, or when their output is truncated, read the logs on the instance.

If you are working with CrowdStrike Support, attach the output from whichever
method you use to your case.

## Method 1 — Using the AWS CLI

> [!NOTE]
> - This method needs the AWS CLI configured with permissions to call SSM
>   (`ssm:ListCommands`, `ssm:ListCommandInvocations`).
> - Distributor runs are **region-specific**. Use the region where the package
>   was deployed everywhere you see `<REGION>` below.

### Step 1 — Find the package run

List the most recent Distributor runs and note the `Id` (Command ID) of the
one you want logs for.

```bash
aws ssm list-commands \
  --max-items 10 \
  --filters key=DocumentName,value=AWS-ConfigureAWSPackage \
  --query 'Commands[].{Id:CommandId,Status:Status,Instances:join(`,`,InstanceIds),Time:RequestedDateTime}' \
  --output table \
  --region <REGION>
```

Example output:

```
----------------------------------------------------------------------------------------------------------------
|                                                 ListCommands                                                 |
+---------------------------------------+----------------------+----------+------------------------------------+
|                  Id                   |      Instances       | Status   |               Time                 |
+---------------------------------------+----------------------+----------+------------------------------------+
|  11111111-1111-1111-1111-111111111111 |  i-0aaaaaaaaaaaaaaaa |  Failed  |  2026-06-12T11:56:12.901000-05:00  |
|  22222222-2222-2222-2222-222222222222 |  i-0bbbbbbbbbbbbbbbb |  Success |  2026-06-12T11:56:22.021000-05:00  |
+---------------------------------------+----------------------+----------+------------------------------------+
```

### Step 2 — Get and save the logs

Copy the Command ID from Step 1 into the command below. It prints the status
and log output for every instance the package ran on, broken out by step, and
saves it to `falcon-ssm-run-logs.json` so you can attach it to a support case.

```bash
aws ssm list-command-invocations \
  --details \
  --query 'CommandInvocations[].{Instance:InstanceId,Status:Status,Plugins:CommandPlugins[].{Name:Name,Status:Status,Code:ResponseCode,Output:Output}}' \
  --output json \
  --command-id <COMMAND_ID> \
  --region <REGION> | tee falcon-ssm-run-logs.json
```

Example output from a failed run:

```json
[
    {
        "Instance": "i-0aaaaaaaaaaaaaaaa",
        "Status": "Failed",
        "Plugins": [
            {
                "Name": "createDownloadFolder",
                "Status": "Success",
                "Code": 0,
                "Output": "Step execution skipped due to unsatisfied preconditions: '\"StringEquals\": [platformType, Windows]'. Step name: createDownloadFolder"
            },
            {
                "Name": "configurePackage",
                "Status": "Failed",
                "Code": 1,
                "Output": "\n----------ERROR-------\nfailed to find platform: no manifest found for platform: mac_os_x, version 26.3.1, architecture arm64\n"
            }
        ]
    }
]
```

**What to look at:** the `configurePackage` step is the one that runs the
Falcon install/uninstall script. Its `Output` field is the package log (it
includes both standard output and any error text). The `createDownloadFolder`
step is internal SSM setup; on non-Windows hosts it is skipped, which is
normal.

## Method 2 — Using the AWS console

1. In the AWS console, go to **Systems Manager** > **Run Command** >
   **Command history**. Make sure you're in the region where the package was
   deployed.
2. Filter the list to find the Distributor runs. Add a filter of
   **Document Name : Equal : AWS-ConfigureAWSPackage**, and optionally narrow
   to a single host with **Instance ID : Equal : `<INSTANCE_ID>`**. Open the
   run you want by clicking its **Command ID**.
3. Under **Targets and outputs**, click the **Instance ID** link for the host
   you want. This opens the **Output on `<instance>`** page.
4. The output is broken out by step. Find **Step 2** (step name
   `configurePackage`) and expand its **Output** and **Error** sections. This
   is the Falcon install/uninstall log: `Output` holds standard output and
   `Error` holds standard error. (**Step 1**, `createDownloadFolder`, is
   internal SSM setup and is skipped on non-Windows hosts, which is normal.)

To share with CrowdStrike Support, copy the `configurePackage` **Output** and
**Error** text.

## Method 3 — On the instance

The complete logs are written on the instance itself, under the orchestration
folder for the Command ID. Use this for runs older than ~30 days, or when the
CLI or console output is truncated (SSM caps inline output at ~2500 characters).

You'll need the **Command ID** of the run (see [Step 1](#step-1--find-the-package-run),
or find it in the AWS console under **Systems Manager** > **Run Command** >
**Command history**). Then, on the instance, open the matching folder:

- **Linux:**
  `/var/lib/amazon/ssm/<INSTANCE_ID>/document/orchestration/<COMMAND_ID>/awsconfigurePackage/configurePackage/`
- **Windows:**
  `%PROGRAMDATA%\Amazon\SSM\InstanceData\<INSTANCE_ID>\document\orchestration\<COMMAND_ID>\awsconfigurePackage\configurePackage\`

That folder contains four files:

| File | Contents |
| --- | --- |
| `stdout` | Raw standard output from the package script |
| `stderr` | Raw standard error from the package script |
| `stdoutConsole` | Standard output with SSM console formatting |
| `stderrConsole` | Standard error with SSM console formatting |

The `stdout` and `stderr` files are the complete package log. Zip up the
`configurePackage` folder and attach it to your support case.
