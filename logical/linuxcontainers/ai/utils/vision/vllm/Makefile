CONTAINER := core:ai-utils
SERVICE   := vllm.service

.PHONY: deploy restart kill status logs

deploy:
	lxc file push $(SERVICE) $(CONTAINER)/etc/systemd/system/$(SERVICE)
	lxc exec $(CONTAINER) -- systemctl daemon-reload
	lxc exec $(CONTAINER) -- systemctl enable --now $(SERVICE)
	lxc exec $(CONTAINER) -- systemctl status $(SERVICE) --no-pager

restart:
	lxc exec $(CONTAINER) -- systemctl restart $(SERVICE)

kill:
	lxc exec $(CONTAINER) -- systemctl kill -s SIGKILL $(SERVICE)
	lxc exec $(CONTAINER) -- systemctl start $(SERVICE)

status:
	lxc exec $(CONTAINER) -- systemctl status $(SERVICE) --no-pager

logs:
	lxc exec $(CONTAINER) -- journalctl -u $(SERVICE) -n 50 --no-pager
