# Bluetooth Bridge - Build and deploy to Nomad
# Usage:
#   make build           - Build Docker image for Nomad
#   make push            - Push Docker image for Nomad
#   make deploy-nomad    - Deploy the Nomad job
#   make status          - Check Nomad job status
#   make logs            - Follow Nomad allocation logs

IMAGE_NAME := registry.linole.org/bluetooth-bridge
VERSION := $(shell date +%Y%m%d%H%M%S)
JOB_NAME := bluetooth-bridge

.PHONY: build push deploy-nomad status logs stop

all: build push deploy-nomad
	@echo "✅ Build, push, and deploy complete (version: $(VERSION))"

build:
	@echo "🔨 Building Docker image $(IMAGE_NAME):$(VERSION)..."
	docker build -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .

push: build
	@echo "📤 Pushing to registry..."
	docker push $(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_NAME):latest

deploy:
	@echo "🚀 Deploying bridge job to Nomad..."
	nomad job run -var="version=latest" job.hcl

# Stop job
stop:
	nomad job stop $(JOB_NAME)

# Follow logs for the latest allocation
logs:
	nomad alloc logs -f $$(nomad job allocs -json $(JOB_NAME) | jq -r '.[0].ID')

# Check status
status:
	nomad job status $(JOB_NAME)
