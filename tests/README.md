# Claude-onTheGo Test Suite

## Running Tests

### 60-Minute Stability Test

Tests long-running session stability for memory leaks, performance degradation, and reliability.

**Prerequisites:**
```bash
pip install websockets psutil
```

**Run test:**
```bash
# Start the backend first
./start.sh

# In another terminal, run the stability test
python3 tests/test_stability.py
```

The test will run for 60 minutes and report:
- Message throughput
- Latency statistics (min/avg/max/p95)
- Memory usage and growth
- CPU usage
- Error rate
- Overall stability score

**Pass Criteria:**
- Stability score ≥ 90/100
- Average latency < 100ms
- Memory growth < 100MB
- Errors < 10

## Quick Test (5 minutes)

For faster testing during development, edit `test_stability.py` and change:

```python
test_duration = 5 * 60  # 5 minutes instead of 60
```
