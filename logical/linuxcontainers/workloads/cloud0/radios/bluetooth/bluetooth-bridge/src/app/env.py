#!/usr/bin/python3
import os

log_level = os.getenv("LOG_LEVEL")
scan_timeout = float(os.getenv("SCAN_TIMEOUT", 60))
connect_timeout = float(os.getenv("CONNECT_TIMEOUT", 60))
command_timeout = float(os.getenv("COMMAND_TIMEOUT", 60))