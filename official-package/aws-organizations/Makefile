all: install build deploy
clean: delete

install:
	@echo "Installing crowdstrike-falconpy and required dependencies.."
	@pip3 install -r requirements.txt -t ./source/python

build:
	@echo "Building AWS SAM artifacts and templates..."
	@sam build --config-file samconfig.toml 

deploy:
	@echo "Initiating AWS SAM Deployment..."
	@sam deploy --config-file samconfig.toml

delete:
	@echo "Removing AWS SAM Deployment..."
	@sam delete --config-file samconfig.toml