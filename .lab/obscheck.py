#!/usr/bin/env python3
import json, os, subprocess, sys, time, urllib.parse, urllib.request, urllib.error
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
passed = failed = 0
FILES = ["-f", "compose.beanie.yaml", "-f", "compose.monitoring.yaml"]
PROM, GRAF = "http://localhost:9090", "http://localhost:3000"


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def get(url, auth=None, timeout=10):
    req = urllib.request.Request(url)
    if auth:
        import base64
        req.add_header("Authorization", "Basic " + base64.b64encode(auth.encode()).decode())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def q(expr):
    return get(PROM + "/api/v1/query?" + urllib.parse.urlencode({"query": expr}))["data"]["result"]


def wait_for(fn, secs, step=5):
    end = time.time() + secs
    while time.time() < end:
        try:
            if fn():
                return True
        except Exception:
            pass
        time.sleep(step)
    return False


def dc(*a):
    return subprocess.run(["docker", "compose"] + FILES + list(a), capture_output=True, text=True)


print("== The stack ==")
r = dc("ps", "--format", "json")
names = set()
for line in r.stdout.strip().split("\n"):
    try:
        names.add(json.loads(line)["Service"])
    except Exception:
        pass
need = {"gateway", "menu", "orders", "payments", "notifications", "traffic", "prometheus", "node-exporter", "cadvisor", "grafana"}
check("all ten services are running (Beanie, traffic, Prometheus, node-exporter, cAdvisor, Grafana)", need <= names, "missing: %s; docker compose -f compose.beanie.yaml -f compose.monitoring.yaml up -d" % sorted(need - names))
if not need <= names:
    finish()

print("== Prometheus ==")
def targets():
    return get(PROM + "/api/v1/targets")["data"]["activeTargets"]
def all_up():
    t = targets()
    jobs = {}
    for x in t:
        jobs.setdefault(x["labels"]["job"], []).append(x["health"] == "up")
    return {"prometheus", "node", "cadvisor", "beanie"} <= set(jobs) and len(jobs["beanie"]) == 5 and all(all(v) for v in jobs.values())
check("four jobs (prometheus, node, cadvisor, beanie) and the five Beanie targets are all up", wait_for(all_up, 90), "http://localhost:9090/targets")
def svc_label():
    return {x["metric"].get("service") for x in q("count by (service) (beanie_http_requests_total)")} >= {"gateway", "menu", "orders", "payments", "notifications"}
check("Beanie's own `service` label survives (honor_labels)", wait_for(svc_label, 60), "without honor_labels it becomes exported_service")
check("node-exporter data is there (the host's CPU counters)", bool(q("node_cpu_seconds_total")))
check("cAdvisor reports per-container memory (series for Docker containers)", wait_for(lambda: len(q('container_memory_working_set_bytes{id=~".*docker.*"}')) >= 5 or len(q('container_memory_working_set_bytes{name!=""}')) >= 5, 90), "newer Docker versions label containers by cgroup id only; Docker Desktop uses /docker/<id>")
rules = get(PROM + "/api/v1/rules")["data"]["groups"]
allr = [r for g in rules for r in g["rules"]]
check("a recording rule beanie:gateway_error_ratio:rate5m exists", any(r["type"] == "recording" and r["name"] == "beanie:gateway_error_ratio:rate5m" for r in allr))
alerts = {r["name"]: r for r in allr if r["type"] == "alerting"}
check("alerts BeanieTargetDown and BeanieHighErrorRate exist with a severity label and a summary", all(n in alerts and alerts[n].get("labels", {}).get("severity") and "summary" in alerts[n].get("annotations", {}) for n in ("BeanieTargetDown", "BeanieHighErrorRate")))
check("BeanieTargetDown is a 30 s alert on up == 0", "BeanieTargetDown" in alerts and alerts["BeanieTargetDown"].get("duration") == 30 and "up" in alerts["BeanieTargetDown"]["query"])

print("== Grafana (everything from files) ==")
auth = "admin:beanie-lab"
def graf_up():
    return get(GRAF + "/api/health")["database"] == "ok"
wait_for(graf_up, 90, 3)
try:
    ds = get(GRAF + "/api/datasources", auth)
    check("a Prometheus data source exists, is the default and was provisioned (read-only)", any(d["type"] == "prometheus" and d.get("isDefault") and d.get("readOnly") for d in ds), "grafana/provisioning/datasources/")
    res = get(GRAF + "/api/search?type=dash-db", auth)
    dash = None
    for d in res:
        full = get(GRAF + "/api/dashboards/uid/" + d["uid"], auth)
        if full["meta"].get("provisioned"):
            dash = full["dashboard"]
    check("a provisioned dashboard exists (loaded from a file, not clicked together)", dash is not None, "grafana/provisioning/dashboards/ and grafana/dashboards/beanie.json")
    ex = " ".join(t.get("expr", "") for p in (dash or {}).get("panels", []) for t in p.get("targets", []))
    check("it has 5+ panels using beanie_ metrics, node_ metrics and container_ metrics", dash is not None and len(dash.get("panels", [])) >= 5 and "beanie_" in ex and "node_" in ex and "container_" in ex)
    check("... and a latency panel with histogram_quantile", "histogram_quantile" in ex)
except Exception as e:
    check("Grafana answers at http://localhost:3000 with admin / beanie-lab", False, str(e)[:80])

print("== Break things on purpose ==")
t0 = time.time()
dc("stop", "menu")
down = wait_for(lambda: any(x["labels"].get("instance", "").startswith("menu") and x["health"] == "down" for x in targets()), 60, 3)
check("stopping menu turns its target down (took %d s)" % int(time.time() - t0), down)
def firing(name):
    return any(a["labels"].get("alertname") == name and a["state"] == "firing" for a in get(PROM + "/api/v1/alerts")["data"]["alerts"])
check("BeanieTargetDown fires (took %d s)" % int(time.time() - t0), wait_for(lambda: firing("BeanieTargetDown"), 120, 3))
dc("start", "menu")
check("... and resolves after menu is started again", wait_for(lambda: not firing("BeanieTargetDown"), 120, 3))
chaos = ["docker", "compose"] + FILES + ["exec", "-T", "menu", "python", "-c", "import urllib.request as u;u.urlopen(u.Request('http://127.0.0.1:8001/chaos',b'{\"error_rate\":0.9}',{'Content-Type':'application/json'},method='PUT')).read()"]
time.sleep(10)
subprocess.run(chaos, capture_output=True)
ok = wait_for(lambda: firing("BeanieHighErrorRate"), 300, 5)
check("making menu fail 90%% of the time fires BeanieHighErrorRate (took %d s)" % int(time.time() - t0), ok, "rate window 5m: it needs a minute or two of errors")
subprocess.run(chaos[:-1] + [chaos[-1].replace("0.9", "0")], capture_output=True)
finish()
