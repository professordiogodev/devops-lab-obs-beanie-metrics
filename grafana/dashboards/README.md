Put your dashboard here as `beanie.json` (Grafana: Dashboard > Share > Export > Export as JSON, "Export for sharing externally" off).
It needs at least five panels: the Beanie request rate and 5xx ratio, the p95 latency, the host CPU busy percentage (node-exporter)
and the memory of each container (cAdvisor). With provisioning it loads by itself when Grafana starts.
