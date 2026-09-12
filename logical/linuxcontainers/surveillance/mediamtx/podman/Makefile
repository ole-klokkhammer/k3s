LXC := core:mediamtx
LXC_BIN ?= lxc
QUADLET_NAME := mediamtx
QUADLET_DIR := etc/containers/systemd
CONFIG_DIR := config
ENV_FILE := /env/surveillance/mediamtx.env

.PHONY: deploy config restart status logs

deploy: config
	$(LXC_BIN) file push $(QUADLET_NAME).container $(LXC)/$(QUADLET_DIR)/$(QUADLET_NAME).container
	$(LXC_BIN) exec $(LXC) -- systemctl daemon-reload
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

config:
	$(LXC_BIN) exec $(LXC) -- mkdir -p /$(CONFIG_DIR)
	$(LXC_BIN) file push mediamtx.yml $(LXC)/$(CONFIG_DIR)/mediamtx.yml.tmpl
	$(LXC_BIN) exec $(LXC) -- sh -c 'set -eu; \
	  set -a; . $(ENV_FILE); set +a; \
	  envsubst < /$(CONFIG_DIR)/mediamtx.yml.tmpl > /$(CONFIG_DIR)/mediamtx.yml.new; \
	  mv /$(CONFIG_DIR)/mediamtx.yml.new /$(CONFIG_DIR)/mediamtx.yml; \
	  rm -f /$(CONFIG_DIR)/mediamtx.yml.tmpl'

restart:
	$(LXC_BIN) exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	$(LXC_BIN) exec $(LXC) -- systemctl status $(QUADLET_NAME)

logs:
	$(LXC_BIN) exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f
