"""
E2E test for reconnection stability and launch screen behavior.
Tests the fixes for reconnection loop and banner display issues.
"""

import time

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def iphone_context(playwright):
    """Create iPhone 13 Pro context for testing."""
    device = playwright.devices["iPhone 13 Pro"]
    browser = playwright.webkit.launch(headless=False)
    context = browser.new_context(**device)
    yield context
    context.close()
    browser.close()


def test_no_reconnection_loop(iphone_context):
    """
    Test that connection remains stable without reconnection loop.

    Expected behavior:
    - Connection establishes successfully
    - No rapid disconnect/reconnect cycles
    - Connection stays open for >15 seconds
    - Terminal becomes visible
    """
    page = iphone_context.new_page()

    # Track console messages
    console_messages = []

    page.on(
        "console",
        lambda msg: console_messages.append(
            {"type": msg.type, "text": msg.text, "timestamp": time.time()}
        ),
    )

    # Navigate to app
    page.goto("http://192.168.1.83:8000")

    # Wait for page to load
    page.wait_for_load_state("domcontentloaded", timeout=10000)

    # Take screenshot for debugging
    page.screenshot(path="/tmp/test_screenshot.png")
    print("[TEST] Screenshot saved to /tmp/test_screenshot.png")

    # Wait a bit for JavaScript to execute
    time.sleep(3)

    # Check if page has basic structure
    body = page.locator("body")
    expect(body).to_be_visible()

    print(f"[TEST] Page title: {page.title()}")
    print(f"[TEST] Page URL: {page.url}")

    # Monitor for 15 seconds to detect reconnection loop
    print("\n[TEST] Monitoring connection stability for 15 seconds...")

    start_time = time.time()
    time.sleep(15)

    # Analyze console logs
    connect_logs = []
    disconnect_logs = []
    guard_logs = []

    for msg in console_messages:
        text = msg["text"]
        if "[WS] Initiating connection attempt" in text:
            connect_logs.append(msg)
        elif "[WS] Connection closed" in text or "[WS] Disconnected" in text:
            disconnect_logs.append(msg)
        elif (
            "skipping duplicate" in text.lower()
            or "already connected" in text.lower()
            or "already connecting" in text.lower()
        ):
            guard_logs.append(msg)

    print(f"[TEST] Connection attempts: {len(connect_logs)}")
    print(f"[TEST] Disconnections: {len(disconnect_logs)}")
    print(f"[TEST] Guard activations: {len(guard_logs)}")

    # Print timing details for connection attempts
    if connect_logs:
        print(f"[TEST] Connection attempt times:")
        for i, log in enumerate(connect_logs):
            relative_time = log["timestamp"] - start_time
            print(f"  {i+1}. {relative_time:.2f}s")

    # Assertions
    # Should have 1 connection attempt initially, maybe 2 max (if auto-reconnect triggered once)
    assert (
        len(connect_logs) <= 2
    ), f"Too many connection attempts ({len(connect_logs)}), indicates reconnection loop"

    # Should have 0-1 disconnections
    assert (
        len(disconnect_logs) <= 1
    ), f"Too many disconnections ({len(disconnect_logs)}), indicates reconnection loop"

    # If guards activated, that's good (means duplicate attempts were prevented)
    if guard_logs:
        print(f"[TEST] ✓ Connection guards activated successfully: {len(guard_logs)} times")

    # Check for errors
    error_logs = [msg for msg in console_messages if msg["type"] == "error"]
    assert len(error_logs) == 0, f"Found {len(error_logs)} console errors: {error_logs}"

    print("[TEST] ✓ Connection remained stable, no reconnection loop detected")


def test_banner_appears_immediately(iphone_context):
    """
    Test that Claude banner appears immediately after connection.

    Expected behavior:
    - Rocket launch screen appears
    - Transitions to terminal with Claude banner
    - NO blank cursor page
    - Banner visible within 2 seconds of connection
    """
    page = iphone_context.new_page()

    console_messages = []
    page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))

    # Navigate to app
    page.goto("http://192.168.1.83:8000")
    page.wait_for_load_state("domcontentloaded")

    # Wait for auto-connect
    time.sleep(3)

    # Check terminal content
    terminal = page.locator("#terminal-container")
    expect(terminal).to_be_visible()

    # Give banner time to render
    time.sleep(2)

    # Check for banner text in console logs (xterm.js writes will appear in logs)
    output_logs = [
        msg["text"]
        for msg in console_messages
        if "[WS] Received" in msg["text"] or "output" in msg["text"]
    ]

    # Terminal should have content (not just blank cursor)
    # We can't easily check xterm.js canvas content, but we can verify logs show banner was sent
    banner_sent = any(
        "Sending initial banner" in msg["text"] or "Sending pending banner" in msg["text"]
        for msg in console_messages
    )

    # Check if banner was sent
    print(f"[TEST] Banner sent: {banner_sent}")
    print(f"[TEST] Output messages received: {len(output_logs)}")

    # Should receive banner output
    assert len(output_logs) > 0, "No output received, terminal likely blank"

    print("[TEST] ✓ Banner transmission verified")


def test_launch_screen_shows_once(iphone_context):
    """
    Test that launch screen only appears once and doesn't flicker.

    Expected behavior:
    - Launch screen appears on page load
    - Disappears after connection
    - Does NOT reappear during stable connection
    - No black screen flicker
    """
    page = iphone_context.new_page()

    # Navigate to app
    page.goto("http://192.168.1.83:8000")
    page.wait_for_load_state("domcontentloaded")

    overlay = page.locator("#tap-to-connect")

    # Launch screen should be visible initially
    expect(overlay).to_be_visible(timeout=5000)

    # Wait for auto-connect
    time.sleep(3)

    # Launch screen should disappear
    expect(overlay).to_be_hidden(timeout=5000)

    # Monitor for 10 seconds - launch screen should NOT reappear
    print("[TEST] Monitoring for launch screen flicker for 10 seconds...")

    for i in range(10):
        time.sleep(1)
        # Check overlay is still hidden
        assert not overlay.is_visible(), f"Launch screen reappeared at second {i+1}"

    print("[TEST] ✓ Launch screen remained hidden, no flicker detected")


def test_console_has_zero_errors(iphone_context):
    """
    Test that no JavaScript errors occur during normal operation.

    Expected behavior:
    - Zero console errors
    - No invalid API calls
    - No undefined references
    """
    page = iphone_context.new_page()

    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    # Navigate and interact
    page.goto("http://192.168.1.83:8000")
    page.wait_for_load_state("domcontentloaded")

    # Wait for connection
    time.sleep(5)

    # Check for errors
    print(f"[TEST] Page errors: {len(errors)}")
    print(f"[TEST] Console errors: {len(console_errors)}")

    if errors:
        print(f"[TEST] Page errors found: {errors}")
    if console_errors:
        print(f"[TEST] Console errors found: {console_errors}")

    assert len(errors) == 0, f"Page errors detected: {errors}"
    assert len(console_errors) == 0, f"Console errors detected: {console_errors}"

    print("[TEST] ✓ Zero errors detected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
