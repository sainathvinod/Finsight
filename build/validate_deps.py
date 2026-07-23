#!/usr/bin/env python3
# FinSight build-time dependency validation (build/release tooling ONLY).
# Reads build/versions.json (single source of truth) and compares installed vs
# required-minimum vs latest-stable. Exit code policy (per the dependency-governance spec):
#   FAIL (exit 1)  -> a REQUIRED dependency is missing OR installed below required_min,
#                     OR Python is below its required_min.
#   WARN (exit 0)  -> installed is at/above min but below latest_stable (drift, reviewable).
#   OK   (exit 0)  -> installed == latest_stable (or >= for tolerant deps).
# This script contains NO network calls and NO self-update behaviour. It never
# modifies the environment; it only reports. It is not part of src/finsight and is
# never imported by the product.
import json, os, sys, sqlite3

try:
    import importlib.metadata as md
except Exception:  # pragma: no cover
    import importlib_metadata as md  # type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "versions.json")


def _parse(v):
    # leading-numeric version tuple; tolerant of suffixes (e.g. "2.13", "0.15.22rc1")
    parts = []
    for tok in str(v).replace("-", ".").split("."):
        num = "".join(ch for ch in tok if ch.isdigit())
        if num == "":
            break
        parts.append(int(num))
    return tuple(parts) or (0,)


def _below(a, b):
    return _parse(a) < _parse(b)


def _installed_python():
    v = sys.version_info
    return "%d.%d.%d" % (v.major, v.minor, v.micro)


def _pkg_version(name):
    try:
        return md.version(name)
    except Exception:
        return None


def main():
    with open(MANIFEST, encoding="utf-8") as fh:
        m = json.load(fh)
    rows = []          # (name, installed, required_min, latest, status)
    fails = 0
    warns = 0

    # Python
    py = m["python"]
    inst = _installed_python()
    if _below(inst, py["required_min"]):
        status = "FAIL (below min %s; recommended %s)" % (py["required_min"], py["recommended"])
        fails += 1
    elif _below(inst, py["latest_stable"]):
        status = "WARN (outdated; latest %s)" % py["latest_stable"]
        warns += 1
    else:
        status = "OK"
    rows.append(("python", inst, py["required_min"], py["latest_stable"], status))

    # SQLite (stdlib-bundled; report only, min is a floor, never a latest-gate FAIL)
    sq = m["sqlite"]
    inst = sqlite3.sqlite_version
    if _below(inst, sq["required_min"]):
        status = "FAIL (below min %s)" % sq["required_min"]
        fails += 1
    elif _below(inst, sq["latest_stable"]):
        status = "WARN (bundled; latest %s)" % sq["latest_stable"]
        warns += 1
    else:
        status = "OK"
    rows.append(("sqlite (bundled)", inst, sq["required_min"], sq["latest_stable"], status))

    # pip-managed packages
    for name, spec in m["packages"].items():
        inst = _pkg_version(name)
        if inst is None:
            if spec.get("required"):
                status = "FAIL (MISSING; pin %s)" % spec["pinned"]
                fails += 1
            else:
                status = "MISSING (optional)"
            rows.append((name, "-", spec["required_min"], spec["latest_stable"], status))
            continue
        if _below(inst, spec["required_min"]):
            status = "FAIL (below min %s)" % spec["required_min"]
            fails += 1
        elif _below(inst, spec["latest_stable"]):
            status = "WARN (outdated; latest %s)" % spec["latest_stable"]
            warns += 1
        else:
            status = "OK"
        rows.append((name, inst, spec["required_min"], spec["latest_stable"], status))

    # render
    w = [max(len(str(r[i])) for r in rows + [("component", "installed", "min", "latest", "status")]) for i in range(5)]
    hdr = ("component", "installed", "min-required", "latest", "status")
    line = "  ".join(str(h).ljust(w[i]) for i, h in enumerate(hdr))
    print("FinSight dependency validation  (manifest as_of %s)" % m["as_of"])
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(r[i]).ljust(w[i]) for i in range(5)))
    print("-" * len(line))
    print("Summary: %d FAIL, %d WARN, %d checked." % (fails, warns, len(rows)))
    if fails:
        print("RESULT: FAIL - a required dependency is missing or below its required minimum.")
        return 1
    print("RESULT: PASS - all required minimums met (warnings are non-blocking drift).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
