LXC := core:transcription
FILE_NAME := mts_1.mp4
DESTINATION_DIR := root/workspace/files
OUT_BASE := mts_1
OUT_DIR := root/workspace

.PHONY: push_files pull_files

push_files:
	lxc file push /home/ole/workspace/oleklokkhammer/projects/cloud/tools/transcription/files/$(FILE_NAME) $(LXC)/$(DESTINATION_DIR)/$(FILE_NAME)

pull_files:
	lxc file pull $(LXC)/$(OUT_DIR)/$(OUT_BASE).json  files/$(OUT_BASE).json
	lxc file pull $(LXC)/$(OUT_DIR)/$(OUT_BASE).srt   files/$(OUT_BASE).srt
	lxc file pull $(LXC)/$(OUT_DIR)/$(OUT_BASE).tsv   files/$(OUT_BASE).tsv
	lxc file pull $(LXC)/$(OUT_DIR)/$(OUT_BASE).txt   files/$(OUT_BASE).txt
	lxc file pull $(LXC)/$(OUT_DIR)/$(OUT_BASE).vtt   files/$(OUT_BASE).vtt
