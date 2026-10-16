#!/usr/bin/env python3
"""Ve bieu do tu results_py.csv -> images/"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("images", exist_ok=True)

rows = []
with open("results_py.csv") as f:
    for r in csv.DictReader(f):
        rows.append((float(r["timestamp"]), r["label"],
                     float(r["elapsed_ms"]), r["success"] == "True"))

t0 = min(r[0] for r in rows)
labels = sorted(set(r[1] for r in rows))
short = {l: l.split(". ", 1)[1] for l in labels}

# 1. Bar chart: avg & p95 per endpoint
avgs, p95s = [], []
for l in labels:
    v = sorted(r[2] for r in rows if r[1] == l)
    avgs.append(sum(v) / len(v))
    p95s.append(v[int(len(v) * 0.95)])
x = range(len(labels))
plt.figure(figsize=(9, 5))
plt.bar([i - 0.2 for i in x], avgs, 0.4, label="Trung binh (avg)")
plt.bar([i + 0.2 for i in x], p95s, 0.4, label="P95")
plt.xticks(list(x), [short[l] for l in labels], rotation=12, ha="right")
plt.ylabel("ms")
plt.title("Thoi gian phan hoi trung binh va P95 theo endpoint (600 requests, 0% loi)")
plt.legend()
plt.tight_layout()
plt.savefig("images/chart_response_time.png", dpi=110)
plt.close()

# 2. Throughput over time (bucket 2s)
buckets = defaultdict(int)
for ts, *_ in rows:
    buckets[int((ts - t0) // 2) * 2] += 1
bx = sorted(buckets)
plt.figure(figsize=(9, 4.5))
plt.plot(bx, [buckets[b] / 2 for b in bx], marker="o", ms=3)
plt.xlabel("Thoi gian chay (giay)")
plt.ylabel("Requests/giay")
plt.title("Throughput theo thoi gian (50 users, ramp-up 20s)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("images/chart_throughput.png", dpi=110)
plt.close()

# 3. Avg response time over time (bucket 5s)
bavg = defaultdict(list)
for ts, _, ms, _ in rows:
    bavg[int((ts - t0) // 5) * 5].append(ms)
bx = sorted(bavg)
plt.figure(figsize=(9, 4.5))
plt.plot(bx, [sum(bavg[b]) / len(bavg[b]) for b in bx], marker="o", ms=3, color="darkorange")
plt.xlabel("Thoi gian chay (giay)")
plt.ylabel("ms")
plt.title("Thoi gian phan hoi trung binh theo thoi gian")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("images/chart_response_time_over_time.png", dpi=110)
plt.close()

print("charts done:", sorted(os.listdir("images")))
