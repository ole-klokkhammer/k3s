LXC := core:frigate
QUADLET_NAME := frigate
QUADLET_DIR := etc/containers/systemd
CONFIG_NAME := config.yaml
CONFIG_DEST ?= /config/config.yaml
# the quadlet (frigate.container) reads EnvironmentFile=/config/frigate.env
ENV_DEST ?= /config/frigate.env

.PHONY: deploy restart status logs config env

deploy: config
	lxc file push $(QUADLET_NAME).container $(LXC)/$(QUADLET_DIR)/$(QUADLET_NAME).container
	lxc exec $(LXC) -- systemctl daemon-reload
	lxc exec $(LXC) -- systemctl restart $(QUADLET_NAME)

# Frigate does NOT template its config (0.17 loads config.yaml verbatim), so
# the ${FRIGATE_HALLWAY_PASSWORD} placeholders are rendered inside the LXC
# from its own $(ENV_DEST) before the file lands as $(CONFIG_DEST).
# The secret therefore never has to live in the version-controlled config.yaml.
config:
	@if [ -f frigate.env ]; then lxc file push frigate.env $(LXC)/$(ENV_DEST); fi
	lxc file push config.yaml $(LXC)/$(CONFIG_DEST).tmpl
	lxc exec $(LXC) -- sh -c 'if command -v envsubst >/dev/null 2>&1; then \
	    set -a; [ -f $(ENV_DEST) ] && . $(ENV_DEST); set +a; \
	    envsubst < $(CONFIG_DEST).tmpl > $(CONFIG_DEST).new && mv $(CONFIG_DEST).new $(CONFIG_DEST); \
	    rm -f $(CONFIG_DEST).tmpl; \
	  else \
	    echo "WARN: no envsubst in $(LXC) - config.yaml pushed UNRENDERED"; \
	    mv $(CONFIG_DEST).tmpl $(CONFIG_DEST); \
	  fi'

status:
	lxc exec $(LXC) -- systemctl status $(QUADLET_NAME)

restart:
	lxc exec $(LXC) -- systemctl restart $(QUADLET_NAME)

logs:
	lxc exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f

