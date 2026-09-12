LXC := core:camagent
# where the PVE 'lxc' CLI lives: override when make runs off-host, e.g.
#   make LXC_BIN='ssh core lxc' deploy          (root ssh user)
#   make LXC_BIN='ssh core sudo lxc' deploy
LXC_BIN ?= lxc
IMAGE := docker.io/nats:2.10-alpine
QUADLET_NAME := nats
QUADLET_DIR := etc/containers/systemd

.PHONY: deploy restart status logs

deploy:
	$(LXC_BIN) exec $(LXC) -- podman pull $(IMAGE)
	$(LXC_BIN) exec $(LXC) -- sh -c 'cat > $(QUADLET_DIR)/$(QUADLET_NAME).container' < nats.container
	$(LXC_BIN) exec $(LXC) -- systemctl daemon-reload
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

restart:
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	$(LXC_BIN) exec $(LXC) -- systemctl status $(QUADLET_NAME)

logs:
	$(LXC_BIN) exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f
