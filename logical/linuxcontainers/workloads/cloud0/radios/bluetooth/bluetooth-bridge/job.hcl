variable "version" {
  type    = string
  default = "latest"
}

variable "log_level" {
  type    = string
  default = "INFO"
}

variable "scan_timeout" {
  type    = string
  default = "60"
}

variable "connect_timeout" {
  type    = string
  default = "60"
}

variable "command_timeout" {
  type    = string
  default = "60"
}

job "hub0-bluetooth-bridge" {
  datacenters = ["dc1"]
  type        = "service"

  constraint {
    attribute = "${meta.machine}"
    operator  = "="
    value     = "hub0"
  }
  
  constraint {
    attribute = "${meta.bluetooth}"
    operator  = "="
    value     = "true"
  }

  group "bridge" {
    count = 1

    network {
      port "health" {}
    }

    restart {
      attempts = 3
      delay    = "10s"
      interval = "1m"
      mode     = "delay"
    }

    task "bridge" {
      driver = "podman" 

      config {
        image        = "registry.linole.org/bluetooth-bridge:${var.version}"
        force_pull   = true
        ports        = ["health"]
        network_mode = "host"
        cap_add      = ["NET_ADMIN", "NET_RAW"]
        security_opt = ["apparmor=unconfined"]
        volumes = [
          "/var/run/dbus:/var/run/dbus"
        ]
      }

      service {
        name     = "bluetooth-bridge"
        provider = "nomad"
        tags     = ["bridge", "bluetooth", "mqtt"]
        port     = "health"

        check {
          name     = "bluetooth-bridge-health"
          type     = "http"
          path     = "/health"
          port     = "health"
          interval = "10s"
          timeout  = "2s"
        }
      }

      template {
        data = <<EOH
{{ with nomadVar "nomad/jobs" }}
MQTT_BROKER={{ .mqtt_broker }}
{{ end }}
EOH
        destination = "secrets/mqtt.env"
        env         = true
      }

      env {
        HEALTH_PORT              = "${NOMAD_PORT_health}"
        LOG_LEVEL                = var.log_level
        SCAN_TIMEOUT             = var.scan_timeout
        CONNECT_TIMEOUT          = var.connect_timeout
        COMMAND_TIMEOUT          = var.command_timeout
        DBUS_SYSTEM_BUS_ADDRESS  = "unix:path=/run/dbus/system_bus_socket"
      }

      resources {
        cpu    = 200
        memory = 256
      }
    }
  }
}