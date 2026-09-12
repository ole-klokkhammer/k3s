LXC := core:camagent
# where the PVE 'lxc' CLI lives: override when make runs off-host, e.g.
#   make LXC_BIN='ssh core lxc' deploy          (root ssh user)
#   make LXC_BIN='ssh core sudo lxc' deploy
LXC_BIN ?= lxc
REGISTRY := registry.linole.org
IMAGE := $(REGISTRY)/embedder:latest
BUILDDIR := /tmp/embedder-build
QUADLET_NAME := embedder
QUADLET_DIR := etc/containers/systemd
ENVFILE := /env/surveillance/embedder.env

.PHONY: image push deploy restart status logs

image:            # build inside the LXC (fresh sources each time)
	$(LXC_BIN) exec $(LXC) -- sh -c 'rm -rf $(BUILDDIR) && mkdir -p $(BUILDDIR)'
	tar -cf - embedder.py Dockerfile | lxc exec $(LXC) -- tar -xf - -C $(BUILDDIR)
	$(LXC_BIN) exec $(LXC) -- podman build -t $(IMAGE) $(BUILDDIR)

push: image
	$(LXC_BIN) exec $(LXC) -- podman push $(IMAGE)

deploy:           # dirs + env (only if missing) + quadlet + restart
	$(LXC_BIN) exec $(LXC) -- sh -c 'mkdir -p /config/embedder /media/detector/events /env/surveillance'
	$(LXC_BIN) exec $(LXC) -- sh -c 'test -f $(ENVFILE) || cat > $(ENVFILE)' < embedder.env.example
	$(LXC_BIN) exec $(LXC) -- sh -c 'cat > $(QUADLET_DIR)/$(QUADLET_NAME).container' < embedder.container
	$(LXC_BIN) exec $(LXC) -- systemctl daemon-reload
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

restart:
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	$(LXC_BIN) exec $(LXC) -- systemctl status $(QUADLET_NAME)

logs:
	$(LXC_BIN) exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f
