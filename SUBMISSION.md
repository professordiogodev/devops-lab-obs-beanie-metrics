# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `compose.monitoring.yaml`: Prometheus, node-exporter, cAdvisor and Grafana
- [ ] `prometheus/prometheus.yml` and `prometheus/rules.yml`
- [ ] `grafana/provisioning/` and `grafana/dashboards/beanie.json`

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste the Prometheus targets (or `up`) with every target up. For each exporter, say in one sentence what it measures: the machine (node-exporter), the containers (cAdvisor), the application (Beanie itself).

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Paste a PromQL query for the container using the most memory, one for the host CPU busy percentage (from the `idle` counter) and one for the gateway request rate. Why do you almost always wrap a counter in `rate()`?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Paste your two rules and say which of them is cause-based (a service is down) and which is symptom-based (customers get errors). Which would you page on?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. You stopped `menu`. Paste how long it took for `up` to turn 0 and for the alert to fire, and from what two settings (scrape interval, `for`) that delay comes.

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Why is your Grafana dashboard and data source provisioned from files instead of clicked together? What happens to a clicked-together dashboard when you run `docker compose down -v`?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. cAdvisor and node-exporter need access to the host (mounts, `pid: host`). Why is that a security trade-off, and why does it behave differently on Docker Desktop for Mac or Windows?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
