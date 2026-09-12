LXC := core:core-cloud
IMAGE := registry.linole.org/lidarr-feeder
TAG := 1.0.37
QUADLET_NAME := lidarr-feeder
QUADLET_DIR := etc/containers/systemd

all: build push deploy

build:
	podman build -t $(IMAGE):$(TAG) .

push:
	podman push $(IMAGE):$(TAG)

deploy:
	lxc file push $(QUADLET_NAME).container $(LXC)/$(QUADLET_DIR)/$(QUADLET_NAME).container
	lxc exec $(LXC) -- systemctl daemon-reload
	lxc exec $(LXC) -- systemctl restart $(QUADLET_NAME)

status:
	lxc exec $(LXC) -- systemctl status $(QUADLET_NAME)

logs:
	lxc exec $(LXC) -- journalctl -u $(QUADLET_NAME) -f


	