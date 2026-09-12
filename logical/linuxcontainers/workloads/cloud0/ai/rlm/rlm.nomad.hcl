job "rlm" {
  datacenters = ["dc1"]
  type = "service"

  constraint {
    attribute = "${node.unique.name}"
    operator  = "="
    value     = "gpu-worker-0"
  }
 
  group "rlm" {
    count = 1

    network {
      port "ws"   { static = 8765 }
      port "http" { static = 8766 }
    }

    task "rlm" {
      driver = "docker"

      config {
        image = "container-registry.home.lan:5000/rlm:latest"
        force_pull = true
        ports = ["ws", "http"]
      }

      env {
        LLM_BASE_URL       = "http://gpu-worker-0:8080/v1"
        LLM_MODEL          = "nvidia/nemotron-3-nano"
        LLM_API_KEY        = "sk-not-needed"
        RLM_MCP_WS_PORT    = "8765"
        RLM_MCP_HTTP_PORT  = "8766"
      }

      resources {
        cpu    = 500
        memory = 1024
      } 
    }
  }
}
