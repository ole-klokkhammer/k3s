LXC := core:camagent
# where the PVE 'lxc' CLI lives: override when make runs off-host, e.g.
#   make LXC_BIN='ssh core lxc' deploy          (root ssh user)
#   make LXC_BIN='ssh core sudo lxc' deploy
LXC_BIN ?= lxc
REGISTRY := registry.linole.org
IMAGE := $(REGISTRY)/detector:latest
BUILDDIR := /tmp/detector-build      # LXC-local dir for build sources
QUADLET_NAME := detector
QUADLET_DIR := etc/containers/systemd
ENVFILE := /env/surveillance/$(QUADLET_NAME).env   # quadlet's EnvironmentFile (LXC layout)

.PHONY: image push deploy restart status logs


image:            # build the detector image inside the LXC (fresh sources each time)
	$(LXC_BIN) exec $(LXC) -- sh -c 'rm -rf $(BUILDDIR) && mkdir -p $(BUILDDIR)'
	tar -cf - detector.py Dockerfile | lxc exec $(LXC) -- tar -xf - -C $(BUILDDIR)
	$(LXC_BIN) exec $(LXC) -- podman build -t $(IMAGE) $(BUILDDIR)

push: image        # registry copy (podman login registry.linole.org inside the LXC first, if it needs auth)
	$(LXC_BIN) exec $(LXC) -- podman push $(IMAGE)

deploy:           # dirs + env (only if missing) + quadlet + restart
	$(LXC_BIN) exec $(LXC) -- sh -c 'mkdir -p /config/$(QUADLET_NAME) /media/$(QUADLET_NAME)/events /env/surveillance'
	$(LXC_BIN) exec $(LXC) -- sh -c 'test -f $(ENVFILE) || cat > $(ENVFILE)' < detector.env.example
	$(LXC_BIN) exec $(LXC) -- sh -c 'cat > $(QUADLET_DIR)/$(QUADLET_NAME).container' < detector.container
	$(LXC_BIN) exec $(LXC) -- systemctl daemon-reload
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

restart:
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	$(LXC_BIN) exec $(LXC) -- systemctl status $(QUADLET_NAME)

logs:
	$(LXC_BIN) exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f
