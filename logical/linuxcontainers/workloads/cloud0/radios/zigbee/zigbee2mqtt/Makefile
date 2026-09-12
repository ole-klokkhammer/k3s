# Zigbee2MQTT - Deploy to Nomad
# Usage:
#   make deploy-nomad    - Deploy the Nomad job
#   make status          - Check Nomad job status
#   make logs            - Follow Nomad allocation logs
#   make stop            - Stop the Nomad job

JOB_NAME := hub0-zigbee2mqtt

.PHONY: all deploy-nomad status logs stop

all: deploy-nomad
	@echo "✅ Deploy complete"

deploy-nomad:
	@echo "🚀 Deploying Zigbee2MQTT job to Nomad..."
	nomad job run -var="version=latest" job.hcl

status:
	nomad job status $(JOB_NAME)

logs:
	nomad alloc logs -f $$(nomad job allocs -json $(JOB_NAME) | jq -r '.[0].ID')

stop:
	nomad job stop $(JOB_NAME)