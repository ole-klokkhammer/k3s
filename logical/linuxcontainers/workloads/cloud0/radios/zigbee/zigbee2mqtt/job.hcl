variable "version" {
  type    = string
  default = "latest"
}

variable "timezone" {
  type    = string
  default = "Europe/Oslo"
}

job "hub0-zigbee2mqtt" {
  datacenters = ["dc1"]
  type        = "service"

  constraint {
    attribute = "${meta.machine}"
    operator  = "="
    value     = "hub0"
  }

  constraint {
    attribute = "${meta.zigbee}"
    operator  = "="
    value     = "true"
  }

  group "zigbee2mqtt" {
    count = 1

    network {
      mode = "host"
      port "http" {
        static = 8080
      }
    }

    restart {
      attempts = 3
      delay    = "10s"
      interval = "1m"
      mode     = "delay"
    }

    task "zigbee2mqtt" {
      driver = "docker"

      config {
        image      = "ghcr.io/koenkk/zigbee2mqtt:${var.version}"
        force_pull = true
        network_mode = "host"

        mount {
          type     = "bind"
          source   = "/opt/zigbee2mqtt/data"
          target   = "/app/data"
          readonly = false
        }

        mount {
          type     = "bind"
          source   = "/run/udev"
          target   = "/run/udev"
          readonly = true
        }

        devices = [
          {
            host_path      = "/dev/ttyUSB0"
            container_path = "/dev/ttyUSB0"
          }
        ]
      }

      env {
        TZ = var.timezone
      }

      service {
        name     = "zigbee2mqtt"
        provider = "nomad"
        tags     = ["bridge", "zigbee", "mqtt"]
        port     = "http"
        address_mode = "host"

        check {
          name     = "zigbee2mqtt-tcp"
          type     = "tcp"
          port     = "http"
          address_mode = "host"
          interval = "10s"
          timeout  = "2s"
        }
      }

      resources {
        cpu    = 300
        memory = 512
      }
    }
  }
}