#!/usr/bin/env python3
"""Kiem thu tai mo phong dung kich ban JMeter trong test-plan.jmx:
- 50 threads, ramp-up 20s, loop 3, think time 0.5s
- 4 HTTP sampler tren https://test.k6.io (QuickPizza demo cua Grafana k6)
Ghi chu: JMeter khong the mo ket noi mang trong moi truong sandbox nay
(tien trinh Java bi chan TCP), nen dung script Python tuong duong de lay so lieu that.
"""
import time
import threading
import csv
import requests

BASE = "https://test.k6.io"
ENDPOINTS = [
    ("1. GET Trang chu", "/", lambda r: r.status_code == 200 and "QuickPizza" in r.text),
    ("2. GET API quotes", "/api/quotes", lambda r: r.status_code == 200 and '"quotes"' in r.text),
    ("3. GET API config", "/api/config", lambda r: r.status_code == 200 and len(r.content) > 0),
    ("4. GET Anh pizza.png", "/images/pizza.png", lambda r: r.status_code == 200 and len(r.content) > 10000),
]
THREADS = 50
RAMP_UP = 20      # giay
LOOPS = 3
THINK_TIME = 0.5  # giay

results = []
lock = threading.Lock()


def worker(idx):
    time.sleep(idx * (RAMP_UP / THREADS))  # ramp-up
    s = requests.Session()
    for _ in range(LOOPS):
        for label, path, check in ENDPOINTS:
            t0 = time.time()
            try:
                r = s.get(BASE + path, timeout=20)
                ms = (time.time() - t0) * 1000
                ok = bool(check(r))
                code, n = r.status_code, len(r.content)
            except Exception:
                ms = (time.time() - t0) * 1000
                ok, code, n = False, 0, 0
            with lock:
                results.append((time.time(), label, round(ms, 1), ok, code, n))
            time.sleep(THINK_TIME)


def main():
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(THREADS)]
    t_start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - t_start

    with open("results_py.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "label", "elapsed_ms", "success", "status_code", "bytes"])
        w.writerows(results)

    total = len(results)
    errs = sum(1 for r in results if not r[3])
    print(f"TOTAL={total} ERRORS={errs} ERR_PCT={errs/total*100:.2f}% "
          f"DURATION={duration:.1f}s THROUGHPUT={total/duration:.1f}/s")
    for label, _, _ in ENDPOINTS:
        sub = [r[2] for r in results if r[1] == label]
        e = sum(1 for r in results if r[1] == label and not r[3])
        sub.sort()
        n = len(sub)
        avg = sum(sub) / n
        p90 = sub[int(n * 0.90)]
        p95 = sub[int(n * 0.95)]
        print(f"{label}: n={n} err={e} avg={avg:.1f}ms min={sub[0]:.1f} "
              f"max={sub[-1]:.1f} p90={p90:.1f} p95={p95:.1f}")


if __name__ == "__main__":
    main()
