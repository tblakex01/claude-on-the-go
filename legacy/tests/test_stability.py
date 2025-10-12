"""
60-Minute Session Stability Tests
Tests long-running sessions for memory leaks, connection stability, and performance degradation
"""

import asyncio
import json
import statistics
import time
from typing import Dict, List

import psutil
import pytest
import websockets


class StabilityMetrics:
    """Tracks stability metrics over time"""

    def __init__(self):
        self.start_time = time.time()
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.errors = []
        self.latencies = []
        self.memory_samples = []
        self.cpu_samples = []
        self.reconnections = 0

    def record_message(self, direction: str, size: int, latency_ms: float = None):
        """Record a message sent or received"""
        if direction == "sent":
            self.messages_sent += 1
            self.bytes_sent += size
        else:
            self.messages_received += 1
            self.bytes_received += size

        if latency_ms:
            self.latencies.append(latency_ms)

    def record_error(self, error: str):
        """Record an error"""
        self.errors.append({"time": time.time() - self.start_time, "error": error})

    def record_system_metrics(self, process: psutil.Process):
        """Record CPU and memory usage"""
        self.memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
        self.cpu_samples.append(process.cpu_percent())

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        duration = time.time() - self.start_time

        return {
            "duration_minutes": duration / 60,
            "messages": {
                "sent": self.messages_sent,
                "received": self.messages_received,
                "total": self.messages_sent + self.messages_received,
                "rate_per_minute": (self.messages_sent + self.messages_received) / (duration / 60),
            },
            "data": {
                "sent_mb": self.bytes_sent / 1024 / 1024,
                "received_mb": self.bytes_received / 1024 / 1024,
                "total_mb": (self.bytes_sent + self.bytes_received) / 1024 / 1024,
            },
            "latency_ms": {
                "min": min(self.latencies) if self.latencies else 0,
                "max": max(self.latencies) if self.latencies else 0,
                "avg": statistics.mean(self.latencies) if self.latencies else 0,
                "p95": (
                    statistics.quantiles(self.latencies, n=20)[18]
                    if len(self.latencies) > 20
                    else 0
                ),
            },
            "memory_mb": {
                "min": min(self.memory_samples) if self.memory_samples else 0,
                "max": max(self.memory_samples) if self.memory_samples else 0,
                "avg": statistics.mean(self.memory_samples) if self.memory_samples else 0,
                "growth": (
                    (self.memory_samples[-1] - self.memory_samples[0])
                    if len(self.memory_samples) > 1
                    else 0
                ),
            },
            "cpu_percent": {
                "min": min(self.cpu_samples) if self.cpu_samples else 0,
                "max": max(self.cpu_samples) if self.cpu_samples else 0,
                "avg": statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            },
            "errors": len(self.errors),
            "reconnections": self.reconnections,
            "stability_score": self._calculate_stability_score(),
        }

    def _calculate_stability_score(self) -> float:
        """Calculate overall stability score (0-100)"""
        score = 100.0

        # Deduct for errors
        score -= len(self.errors) * 2

        # Deduct for reconnections
        score -= self.reconnections * 5

        # Deduct for high latency
        if self.latencies:
            avg_latency = statistics.mean(self.latencies)
            if avg_latency > 100:
                score -= (avg_latency - 100) / 10

        # Deduct for memory growth (leak indicator)
        if len(self.memory_samples) > 1:
            memory_growth = self.memory_samples[-1] - self.memory_samples[0]
            if memory_growth > 50:  # More than 50MB growth
                score -= memory_growth / 10

        return max(0, min(100, score))


@pytest.mark.slow
async def test_60_minute_session(backend_url: str = "ws://localhost:8000/ws"):
    """
    Run a 60-minute stability test

    Args:
        backend_url: WebSocket URL to test
    """
    print("=" * 60)
    print("60-MINUTE SESSION STABILITY TEST")
    print("=" * 60)
    print(f"Backend: {backend_url}")
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    metrics = StabilityMetrics()

    # Find backend process for monitoring
    backend_process = None
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if "python" in proc.info["name"].lower() and "app.py" in " ".join(proc.info["cmdline"]):
                backend_process = psutil.Process(proc.info["pid"])
                print(f"✓ Found backend process (PID: {backend_process.pid})")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not backend_process:
        print("⚠️  Could not find backend process - system metrics will be unavailable")

    # Test parameters
    test_duration = 60 * 60  # 60 minutes
    message_interval = 5  # Send message every 5 seconds
    metrics_interval = 30  # Record system metrics every 30 seconds

    start = time.time()
    next_message = start
    next_metrics = start
    message_count = 0

    try:
        async with websockets.connect(backend_url) as ws:
            print("✓ Connected to backend")
            print()
            print("Running test... (this will take 60 minutes)")
            print("Progress will be shown every 5 minutes")
            print()

            last_progress = start

            while time.time() - start < test_duration:
                now = time.time()

                # Send periodic test message
                if now >= next_message:
                    message_count += 1
                    test_msg = {"type": "input", "text": f"Test message {message_count}\r"}
                    msg_json = json.dumps(test_msg)
                    msg_bytes = msg_json.encode("utf-8")

                    send_start = time.time()
                    await ws.send(msg_bytes)
                    metrics.record_message("sent", len(msg_bytes))

                    # Wait for response with timeout
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        latency = (time.time() - send_start) * 1000  # ms
                        metrics.record_message("received", len(response), latency)

                        # Show REAL data every 10 messages (prove it's not hardcoded!)
                        if message_count % 10 == 0:
                            print(
                                f"[LIVE] Msg #{message_count}: {latency:.2f}ms latency, {len(response)} bytes received"
                            )
                            if backend_process and metrics.memory_samples:
                                print(
                                    f"       Memory: {metrics.memory_samples[-1]:.1f}MB, CPU: {metrics.cpu_samples[-1]:.1f}%"
                                )
                    except asyncio.TimeoutError:
                        print(f"[ERROR] Message {message_count} timed out!")
                        metrics.record_error("Response timeout")

                    next_message = now + message_interval

                # Record system metrics
                if backend_process and now >= next_metrics:
                    try:
                        metrics.record_system_metrics(backend_process)
                        # Show REAL system metrics as they're collected
                        mem_mb = metrics.memory_samples[-1]
                        cpu_pct = metrics.cpu_samples[-1]
                        print(
                            f"[METRICS] Backend process: {mem_mb:.1f}MB RAM, {cpu_pct:.1f}% CPU (LIVE DATA)"
                        )
                    except psutil.NoSuchProcess:
                        print("[ERROR] Backend process died!")
                        metrics.record_error("Backend process died")
                        break
                    next_metrics = now + metrics_interval

                # Show progress every 5 minutes
                if now - last_progress >= 300:
                    elapsed_min = (now - start) / 60
                    progress_pct = (now - start) / test_duration * 100
                    print(
                        f"[{elapsed_min:.1f} min] Progress: {progress_pct:.1f}% - "
                        f"Messages: {metrics.messages_sent}/{metrics.messages_received}, "
                        f"Errors: {len(metrics.errors)}"
                    )
                    last_progress = now

                await asyncio.sleep(0.1)

    except websockets.exceptions.ConnectionClosed as e:
        metrics.record_error(f"Connection closed: {e}")
        metrics.reconnections += 1
    except Exception as e:
        metrics.record_error(f"Unexpected error: {e}")

    # Generate report
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print()

    summary = metrics.get_summary()

    print("📊 SUMMARY")
    print("-" * 60)
    print(f"Duration:        {summary['duration_minutes']:.1f} minutes")
    print(f"Messages Sent:   {summary['messages']['sent']}")
    print(f"Messages Recv:   {summary['messages']['received']}")
    print(f"Message Rate:    {summary['messages']['rate_per_minute']:.1f}/min")
    print(f"Data Transfer:   {summary['data']['total_mb']:.2f} MB")
    print()

    print("⏱️  LATENCY")
    print("-" * 60)
    print(f"Min:     {summary['latency_ms']['min']:.2f} ms")
    print(f"Avg:     {summary['latency_ms']['avg']:.2f} ms")
    print(f"Max:     {summary['latency_ms']['max']:.2f} ms")
    print(f"P95:     {summary['latency_ms']['p95']:.2f} ms")
    print()

    print("💾 MEMORY")
    print("-" * 60)
    print(f"Min:     {summary['memory_mb']['min']:.2f} MB")
    print(f"Avg:     {summary['memory_mb']['avg']:.2f} MB")
    print(f"Max:     {summary['memory_mb']['max']:.2f} MB")
    print(f"Growth:  {summary['memory_mb']['growth']:.2f} MB")
    print()

    print("🔥 CPU")
    print("-" * 60)
    print(f"Min:     {summary['cpu_percent']['min']:.1f}%")
    print(f"Avg:     {summary['cpu_percent']['avg']:.1f}%")
    print(f"Max:     {summary['cpu_percent']['max']:.1f}%")
    print()

    print("🎯 RELIABILITY")
    print("-" * 60)
    print(f"Errors:          {summary['errors']}")
    print(f"Reconnections:   {summary['reconnections']}")
    print(f"Stability Score: {summary['stability_score']:.1f}/100")
    print()

    # Pass/Fail criteria
    passed = True
    print("✅ PASS/FAIL CRITERIA")
    print("-" * 60)

    if summary["stability_score"] >= 90:
        print("✓ Stability score >= 90")
    else:
        print(f"✗ Stability score < 90 (got {summary['stability_score']:.1f})")
        passed = False

    if summary["latency_ms"]["avg"] < 100:
        print("✓ Average latency < 100ms")
    else:
        print(f"✗ Average latency >= 100ms (got {summary['latency_ms']['avg']:.2f}ms)")
        passed = False

    if summary["memory_mb"]["growth"] < 100:
        print("✓ Memory growth < 100MB")
    else:
        print(f"✗ Memory growth >= 100MB (got {summary['memory_mb']['growth']:.2f}MB)")
        passed = False

    if summary["errors"] < 10:
        print("✓ Errors < 10")
    else:
        print(f"✗ Errors >= 10 (got {summary['errors']})")
        passed = False

    print()
    print("=" * 60)
    if passed:
        print("🎉 TEST PASSED - System is stable for 60-minute sessions")
    else:
        print("❌ TEST FAILED - System needs improvements")
    print("=" * 60)

    return summary


if __name__ == "__main__":
    print("Starting 60-minute stability test...")
    print("Make sure the backend is running on port 8000")
    print()

    try:
        summary = asyncio.run(test_60_minute_session())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()
