import os

print("Removing AWS SAM Deployment...")
os.system("sam delete --config-file samconfig.toml")