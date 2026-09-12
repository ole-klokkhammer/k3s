variable "version" {
  type    = string
  default = "latest"
}

variable "log_level" {
  type    = string
  default = "DEBUG"
}

variable "ha_discovery" {
  type    = string
  default = "true"
}

job "bthome" {
  datacenters = ["dc1"]
  type        = "service"

  group "bthome" {
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

    task "processor" {
      driver = "docker"

      config {
        image      = "ghcr.io/ole-klokkhammer/bthome:${var.version}"
        force_pull = true
        ports      = ["health"]
      }

      service {
        name     = "bthome"
        provider = "nomad"
        tags     = ["processor", "mqtt"]
        port     = "health"

        check {
          name     = "bthome-health"
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
        HEALTH_PORT  = "${NOMAD_PORT_health}"
        LOG_LEVEL    = var.log_level
        HA_DISCOVERY = var.ha_discovery
      }

      resources {
        cpu    = 100
        memory = 128
      }
    }
  }
}
