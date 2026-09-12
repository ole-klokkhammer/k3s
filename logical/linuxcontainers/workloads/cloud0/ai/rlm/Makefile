# RLM Runtime Makefile
# ====================

REGISTRY := container-registry.home.lan:5000
IMAGE := rlm
VERSION := latest
TAG := $(REGISTRY)/$(IMAGE):$(VERSION)

NOMAD_JOB := rlm.nomad.hcl

.PHONY: help build push deploy run stop test clean

help:
	@echo "RLM Runtime - Available targets:"
	@echo "  make build    - Build Docker image"
	@echo "  make push     - Push image to registry"
	@echo "  make deploy   - Deploy to Nomad"
	@echo "  make run      - Run container locally"
	@echo "  make stop     - Stop local container"
	@echo "  make test     - Test MCP server (stdio)"
	@echo "  make test-ws  - Test WebSocket server"
	@echo "  make clean    - Remove local image"

# Build the Docker image
build:
	docker build -t $(TAG) .

# Push to registry
push: build
	docker push $(TAG)

# Deploy to Nomad
deploy: push
	nomad job run $(NOMAD_JOB)

# Run locally (WebSocket mode)
run:
	docker run -d --name rlm-mcp \
		-p 8181:8181 \
		-e LLM_BASE_URL=http://gpu-worker-0:8080/v1 \
		-e LLM_MODEL=nvidia/nemotron-3-nano \
		-e LLM_API_KEY=sk-not-needed \
		$(TAG)
	@echo "RLM MCP running at ws://localhost:8181"

# Stop local container
stop:
	docker stop rlm-mcp 2>/dev/null || true
	docker rm rlm-mcp 2>/dev/null || true

# Test stdio MCP server
test:
	@echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
		python3 -m rlm_runtime.mcp_server

# Test WebSocket MCP server (requires websocat)
test-ws:
	@echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
		websocat ws://localhost:8181/

# Clean up
clean: stop
	docker rmi $(TAG) 2>/dev/null || true
