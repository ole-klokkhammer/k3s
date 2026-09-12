# AI Utilities Appliance

## setup
lxc profile create ai-utils
lxc profile edit ai-utils
lxc launch ubuntu:24.04 ai-utils -p default -p ai-utils
lxc exec ai-utils -- bash

