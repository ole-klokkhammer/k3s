HOST      := core
CONTAINER := torrent
REMOTE    := $(HOST):$(CONTAINER)
SERVICE   := torrent-stack.service
STACK_DIR := /torrent/stack
COMPOSE_FILE := $(STACK_DIR)/docker-compose.yaml
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

configure: install-docker

# --- Docker ---

install-docker:
	lxc exec $(REMOTE) -- bash -lc "\
	apt-get update && \
	apt-get install -y docker.io ca-certificates curl gnupg && \
	systemctl enable --now docker && \
	install -m 0755 -d /etc/apt/keyrings && \
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
	echo \"deb [arch=\$$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$$(lsb_release -cs) stable\" > /etc/apt/sources.list.d/docker.list && \
	apt-get update && \
	apt-get install -y docker-compose-plugin"

# --- Deployment ---

start:
	lxc exec $(REMOTE) -- systemctl daemon-reload
	lxc exec $(REMOTE) -- systemctl enable --now $(SERVICE)
	lxc exec $(REMOTE) -- systemctl status $(SERVICE) --no-pager

# push the files the vm needs (lxc file push can't push directories),
# then recreate changed containers
sync:
	lxc exec $(REMOTE) -- mkdir -p $(STACK_DIR)
	lxc file push docker-compose.yaml $(REMOTE)$(STACK_DIR)/docker-compose.yaml
	lxc file push torrent-stack.env $(REMOTE)$(STACK_DIR)/torrent-stack.env

up:
	lxc exec $(REMOTE) -- $(DOCKER_COMPOSE) up -d

# one-time (or after editing the unit): install the systemd unit
install-service:
	lxc file push torrent-stack.service $(REMOTE)/etc/systemd/system/torrent-stack.service
	lxc exec $(REMOTE) -- systemctl daemon-reload

# --- Operations ---

restart:
	lxc exec $(REMOTE) -- systemctl restart $(SERVICE)

stop:
	lxc exec $(REMOTE) -- systemctl stop $(SERVICE)

status:
	@echo "=== Service ==="
	lxc exec $(REMOTE) -- systemctl status $(SERVICE) --no-pager || true
	@echo ""
	@echo "=== Containers ==="
	lxc exec $(REMOTE) -- $(DOCKER_COMPOSE) ps
	@echo ""

logs:
	lxc exec $(REMOTE) -- $(DOCKER_COMPOSE) logs --tail=50

logs-traefik:
	lxc exec $(REMOTE) -- $(DOCKER_COMPOSE) logs traefik --tail=50

shell:
	lxc exec $(REMOTE) -- bash
