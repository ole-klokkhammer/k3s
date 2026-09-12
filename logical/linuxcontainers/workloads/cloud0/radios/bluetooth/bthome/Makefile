# BTHome Processor - Build and Deploy
# Usage:
#   make build    - Build Docker image
#   make push     - Push to registry
#   make deploy   - Deploy latest pushed image to Nomad
#   make all      - Build, push, and deploy the same version

IMAGE_NAME := ghcr.io/ole-klokkhammer/bthome
VERSION := $(shell date +%Y%m%d%H%M%S)

.PHONY: build push deploy deploy-version all logs status stop

build:
	@echo "🔨 Building Docker image $(IMAGE_NAME):$(VERSION)..."
	docker build -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .

push: build
	@echo "📤 Pushing to registry..."
	docker push $(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_NAME):latest

deploy:
	@echo "🚀 Deploying latest image to Nomad..."
	nomad job run -var="version=latest" job.hcl

deploy-version:
	@echo "🚀 Deploying to Nomad with version $(VERSION)..."
	nomad job run -var="version=$(VERSION)" job.hcl

all: push deploy-version
	@echo "✅ Build, push, and deploy complete (version: $(VERSION))"

logs:
	nomad alloc logs -f $$(nomad job allocs -json bthome | jq -r '.[0].ID')

status:
	nomad job status bthome

stop:
	nomad job stop bthome
