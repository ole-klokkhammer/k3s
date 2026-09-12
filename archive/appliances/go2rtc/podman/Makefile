LXC := core:go2rtc
QUADLET_NAME := go2rtc
QUADLET_DIR := etc/containers/systemd
CONFIG_NAME := go2rtc
CONFIG_DIR := config

.PHONY: deploy restart status logs

deploy:
	lxc file push $(QUADLET_NAME).container $(LXC)/$(QUADLET_DIR)/$(QUADLET_NAME).container
	lxc file push $(CONFIG_NAME).yaml $(LXC)/$(CONFIG_DIR)/$(CONFIG_NAME).yaml
	lxc exec $(LXC) -- systemctl daemon-reload
	lxc exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	lxc exec $(LXC) -- systemctl status $(QUADLET_NAME)

restart:
	lxc exec $(LXC) -- systemctl restart $(QUADLET_NAME)

logs:
	lxc exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f

