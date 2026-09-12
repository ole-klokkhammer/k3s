LXC := core:camagent
# where the PVE 'lxc' CLI lives: override when make runs off-host, e.g.
#   make LXC_BIN='ssh core lxc' deploy          (root ssh user)
#   make LXC_BIN='ssh core sudo lxc' deploy
LXC_BIN ?= lxc
REGISTRY := registry.linole.org
IMAGE := $(REGISTRY)/query:latest
BUILDDIR := /tmp/query-build
QUADLET_NAME := query
QUADLET_DIR := etc/containers/systemd
ENVFILE := /env/surveillance/query.env

.PHONY: image push deploy restart status logs

image:            # build inside the LXC (fresh sources each time)
	$(LXC_BIN) exec $(LXC) -- sh -c 'rm -rf $(BUILDDIR) && mkdir -p $(BUILDDIR)'
	tar -cf - agent.py Dockerfile | lxc exec $(LXC) -- tar -xf - -C $(BUILDDIR)
	$(LXC_BIN) exec $(LXC) -- podman build -t $(IMAGE) $(BUILDDIR)

push: image
	$(LXC_BIN) exec $(LXC) -- podman push $(IMAGE)

deploy:           # dirs + env (only if missing) + quadlet + restart
	$(LXC_BIN) exec $(LXC) -- sh -c 'mkdir -p /config/query /env/surveillance'
	$(LXC_BIN) exec $(LXC) -- sh -c 'test -f $(ENVFILE) || cat > $(ENVFILE)' < query.env.example
	$(LXC_BIN) exec $(LXC) -- sh -c 'cat > $(QUADLET_DIR)/$(QUADLET_NAME).container' < query.container
	$(LXC_BIN) exec $(LXC) -- systemctl daemon-reload
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

restart:
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	$(LXC_BIN) exec $(LXC) -- systemctl status $(QUADLET_NAME)

logs:
	$(LXC_BIN) exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f
