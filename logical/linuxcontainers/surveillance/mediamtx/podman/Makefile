LXC := core:surveillance
QUADLET_NAME := mediamtx
QUADLET_DIR := etc/containers/systemd
CONFIG_DIR := config/mediamtx

.PHONY: deploy config restart status logs

deploy: config
	lxc file push $(QUADLET_NAME).container $(LXC)/$(QUADLET_DIR)/$(QUADLET_NAME).container
	lxc exec $(LXC) -- systemctl daemon-reload
	lxc exec $(LXC) -- systemctl restart $(QUADLET_NAME)

config:
	lxc file push mediamtx.yml $(LXC)/$(CONFIG_DIR)/mediamtx.yml.tmpl
	lxc exec $(LXC) -- sh -c 'set -eu; \
	  set -a; . /config/mediamtx/.env; set +a; \
	  envsubst < /$(CONFIG_DIR)/mediamtx.yml.tmpl > /$(CONFIG_DIR)/mediamtx.yml.new; \
	  mv /$(CONFIG_DIR)/mediamtx.yml.new /$(CONFIG_DIR)/mediamtx.yml; \
	  rm -f /$(CONFIG_DIR)/mediamtx.yml.tmpl'

restart:
	lxc exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	lxc exec $(LXC) -- systemctl status $(QUADLET_NAME)

logs:
	lxc exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f
