#!/usr/bin/env python3
"""
traffic-generator.py
Continuous load testing and zero-downtime verification tool.
Sends concurrent HTTP requests, records status codes, tracks response latencies,
and reports observed application versions during live deployments.
"""

import argparse
import concurrent.futures
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def send_request(url: str, timeout: float = 3.0) -> dict:
    start_time = time.time()
    result = {
        "timestamp": time.time(),
        "status_code": 0,
        "latency_ms": 0.0,
        "version": "unknown",
        "error": None,
    }

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ZeroDowntimeVerificationAgent/1.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result["status_code"] = response.getcode()
            result["latency_ms"] = (time.time() - start_time) * 1000.0
            body = response.read().decode("utf-8")
            try:
                data = json.loads(body)
                result["version"] = data.get("version", "unknown")
            except Exception:
                pass
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["latency_ms"] = (time.time() - start_time) * 1000.0
        result["error"] = str(e)
    except Exception as e:
        result["status_code"] = 0
        result["latency_ms"] = (time.time() - start_time) * 1000.0
        result["error"] = str(e)

    return result


def run_load_test(url: str, duration: int, concurrency: int, output_file: str = None):
    print("=" * 70)
    print(" 🚀 STARTING ZERO-DOWNTIME AVAILABILITY & TRAFFIC VERIFICATION")
    print(f" Target URL:   {url}")
    print(f" Duration:     {duration} seconds")
    print(f" Concurrency:  {concurrency} worker threads")
    print("=" * 70)

    results = []
    end_time = time.time() + duration
    total_dispatched = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        while time.time() < end_time:
            batch_size = concurrency
            futures = [executor.submit(send_request, url) for _ in range(batch_size)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                results.append(res)
                total_dispatched += 1

                # Live ticker print
                status_symbol = "✓" if 200 <= res["status_code"] < 400 else "✗"
                sys.stdout.write(
                    f"\r[{status_symbol}] Requests: {total_dispatched} | "
                    f"Code: {res['status_code']} | "
                    f"Ver: {res['version']} | "
                    f"Latency: {res['latency_ms']:.1f}ms   "
                )
                sys.stdout.flush()

            time.sleep(0.05)

    print("\n" + "=" * 70)
    print(" 📊 DEPLOYMENT VERIFICATION SUMMARY REPORT")
    print("=" * 70)

    if not results:
        print("No requests were recorded.")
        return

    total_requests = len(results)
    status_counts = {}
    version_counts = {}
    latencies = [r["latency_ms"] for r in results]

    for r in results:
        code = str(r["status_code"])
        status_counts[code] = status_counts.get(code, 0) + 1
        ver = r["version"]
        version_counts[ver] = version_counts.get(ver, 0) + 1

    success_count = sum(count for code, count in status_counts.items() if code.startswith("2"))
    failed_count = total_requests - success_count
    availability_pct = (success_count / total_requests) * 100.0

    p50 = statistics.median(latencies)
    latencies.sort()
    p90 = latencies[int(len(latencies) * 0.90)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"Total Dispatched Requests:  {total_requests}")
    print(f"Successful Requests (2xx):  {success_count}")
    print(f"Failed Requests (Non-2xx):  {failed_count}")
    print(f"Observed Availability:      {availability_pct:.2f}%")
    print("-" * 70)
    print(f"Latency min / avg / max:    {min(latencies):.1f}ms / {statistics.mean(latencies):.1f}ms / {max(latencies):.1f}ms")
    print(f"Latency p50 / p90 / p95:    {p50:.1f}ms / {p90:.1f}ms / {p95:.1f}ms / p99: {p99:.1f}ms")
    print("-" * 70)
    print("Observed Version Distribution (Traffic Split Evidence):")
    for ver, count in version_counts.items():
        pct = (count / total_requests) * 100.0
        print(f"  Version '{ver}': {count} requests ({pct:.1f}%)")
    print("-" * 70)
    print("HTTP Status Codes:")
    for code, count in sorted(status_counts.items()):
        print(f"  HTTP {code}: {count} requests")
    print("=" * 70)

    report_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_url": url,
        "duration_seconds": duration,
        "concurrency": concurrency,
        "total_requests": total_requests,
        "successful_requests": success_count,
        "failed_requests": failed_count,
        "availability_percentage": round(availability_pct, 3),
        "latency_percentiles_ms": {
            "min": round(min(latencies), 2),
            "mean": round(statistics.mean(latencies), 2),
            "p50": round(p50, 2),
            "p90": round(p90, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "max": round(max(latencies), 2),
        },
        "version_distribution": version_counts,
        "status_distribution": status_counts,
    }

    if output_file:
        with open(output_file, "w") as f:
            json.dump(report_data, f, indent=2)
        print(f"Full machine-readable report written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Zero-Downtime Traffic Verification Generator")
    parser.add_argument("--url", default="http://localhost:8000/api/products", help="Target endpoint")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent worker threads")
    parser.add_argument("--output", default="test-report.json", help="Path to write JSON summary")
    args = parser.parse_args()

    run_load_test(args.url, args.duration, args.concurrency, args.output)


if __name__ == "__main__":
    main()
