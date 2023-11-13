import os

print("Installing crowdstrike-falconpy and required dependencies..")
os.system("pip3 install -r requirements.txt -t ./source/python")
print("Building AWS SAM artifacts and templates...")
os.system("sam build --config-file samconfig.toml")
print("Initiating AWS SAM Deployment...")
os.system("sam deploy --config-file samconfig.toml")