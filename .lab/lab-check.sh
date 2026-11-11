#!/usr/bin/env bash
rc=0
grep -q 'prometheus' compose.monitoring.yaml && grep -q 'cadvisor' compose.monitoring.yaml && echo "- ✅ compose.monitoring.yaml has the stack" || { echo "- ❌ compose.monitoring.yaml is not written yet"; rc=1; }
grep -q 'honor_labels' prometheus/prometheus.yml && echo "- ✅ prometheus.yml sets honor_labels" || { echo "- ❌ prometheus.yml has no honor_labels for Beanie"; rc=1; }
test -s grafana/dashboards/beanie.json && echo "- ✅ the dashboard JSON is in git" || { echo "- ❌ grafana/dashboards/beanie.json is missing"; rc=1; }
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
