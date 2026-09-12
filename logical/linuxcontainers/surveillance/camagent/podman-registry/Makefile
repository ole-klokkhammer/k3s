CONTAINER := core:core-cloud
REGISTRY_SERVICE   := podman-registry-login.service 
 

deploy-registry:
	lxc file push $(REGISTRY_SERVICE) $(CONTAINER)/etc/systemd/system/$(REGISTRY_SERVICE)
	lxc exec $(CONTAINER) -- systemctl daemon-reload
	lxc exec $(CONTAINER) -- systemctl enable --now $(REGISTRY_SERVICE)
	lxc exec $(CONTAINER) -- systemctl status $(REGISTRY_SERVICE) --no-pager

registry-logs:
	lxc exec $(CONTAINER) -- journalctl -u $(REGISTRY_SERVICE) -n 50 --no-pager
