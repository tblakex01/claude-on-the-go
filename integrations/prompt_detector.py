"""
Claude Prompt Detection for push notifications

Detects when Claude CLI is waiting for user input by analyzing terminal output.
Supports various Claude prompt patterns and debouncing to prevent notification spam.
"""

import re
import time
from typing import Optional


class PromptDetector:
    """
    Detects when Claude is waiting for user input.

    Uses pattern matching on terminal output to identify prompt states.
    Includes debouncing to prevent sending multiple notifications for the same prompt.
    """

    # Claude prompt patterns
    PROMPT_PATTERNS = [
        # Common Claude prompts
        r"What would you like to do\?",
        r"How would you like to proceed\?",
        r"Would you like me to",
        r"What\s+would\s+you\s+like\s+to",
        r"Do\s+you\s+want\s+me\s+to",
        r"Should\s+I",
        r"Would\s+you\s+like\s+to",
        # Task continuation prompts
        r"Continue\s+with",
        r"Proceed\s+with",
        r"Start\s+working\s+on",
        # Approval/confirmation prompts
        r"Is\s+this\s+correct\?",
        r"Confirm\s+to\s+proceed",
        r"Press\s+Enter\s+to\s+continue",
        # User input requests
        r"Please\s+provide",
        r"I\s+need\s+you\s+to",
        r"Can\s+you\s+provide",
        # Exit prompts (these should NOT trigger notifications)
        r"Press\s+any\s+key\s+to\s+exit",
        r"Goodbye",
    ]

    # Patterns that should NOT trigger notifications
    IGNORE_PATTERNS = [
        r"Press\s+any\s+key\s+to\s+exit",
        r"Goodbye",
        r"Exiting",
        r"Shutting\s+down",
    ]

    def __init__(self, debounce_seconds: float = 30.0, buffer_size: int = 2000):
        """
        Initialize prompt detector.

        Args:
            debounce_seconds: Minimum time between notifications for same prompt
            buffer_size: Size of output buffer to analyze (chars)
        """
        self.debounce_seconds = debounce_seconds
        self.buffer_size = buffer_size

        # Compile regex patterns for performance
        self.prompt_regex = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_PATTERNS]
        self.ignore_regex = [re.compile(p, re.IGNORECASE) for p in self.IGNORE_PATTERNS]

        # State tracking
        self.output_buffer = ""
        self.last_prompt_time: Optional[float] = None
        self.last_prompt_text: Optional[str] = None

    def add_output(self, text: str) -> None:
        """
        Add new terminal output to buffer.

        Args:
            text: New output from Claude terminal
        """
        self.output_buffer += text

        # Keep buffer at manageable size
        if len(self.output_buffer) > self.buffer_size:
            self.output_buffer = self.output_buffer[-self.buffer_size :]

    def detect_prompt(self) -> Optional[str]:
        """
        Check if buffer contains a Claude prompt.

        Returns:
            Prompt text if detected and not debounced, None otherwise
        """
        # Check ignore patterns first
        for regex in self.ignore_regex:
            if regex.search(self.output_buffer):
                return None

        # Check prompt patterns
        for regex in self.prompt_regex:
            match = regex.search(self.output_buffer)
            if match:
                prompt_text = match.group(0)

                # Check debouncing
                now = time.time()

                # Same prompt within debounce window?
                if (
                    self.last_prompt_text == prompt_text
                    and self.last_prompt_time is not None
                    and (now - self.last_prompt_time) < self.debounce_seconds
                ):
                    return None

                # New prompt or debounce expired
                self.last_prompt_time = now
                self.last_prompt_text = prompt_text

                return prompt_text

        return None

    def should_notify(self) -> bool:
        """
        Check if a notification should be sent based on current buffer.

        Returns:
            True if prompt detected and notification should be sent
        """
        return self.detect_prompt() is not None

    def extract_prompt_context(self, char_limit: int = 200) -> str:
        """
        Extract context around the detected prompt for notification.

        Args:
            char_limit: Maximum characters to include in context

        Returns:
            Context text suitable for notification body
        """
        if not self.output_buffer:
            return "Claude is waiting for your input"

        # Get last N characters from buffer
        context = self.output_buffer[-char_limit:]

        # Clean ANSI escape codes
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        context = ansi_escape.sub("", context)

        # Clean extra whitespace
        context = re.sub(r"\s+", " ", context).strip()

        # Truncate if still too long
        if len(context) > char_limit:
            context = context[: char_limit - 3] + "..."

        return context or "Claude is waiting for your input"

    def reset(self) -> None:
        """Reset detector state"""
        self.output_buffer = ""
        self.last_prompt_time = None
        self.last_prompt_text = None


# Example usage
if __name__ == "__main__":
    # Test the detector
    detector = PromptDetector(debounce_seconds=5.0)

    test_outputs = [
        "Starting task...\n",
        "Processing files...\n",
        "What would you like to do?\n",  # Should trigger
        "What would you like to do?\n",  # Should NOT trigger (debounced)
        "More output...\n",
        "How would you like to proceed?\n",  # Should trigger (different prompt)
        "Press any key to exit\n",  # Should NOT trigger (ignore pattern)
    ]

    for i, output in enumerate(test_outputs, 1):
        print(f"\n{i}. Adding output: {output.strip()}")
        detector.add_output(output)

        if detector.should_notify():
            prompt = detector.detect_prompt()
            context = detector.extract_prompt_context(50)
            print(f"   ✅ NOTIFY: {prompt}")
            print(f"   Context: {context}")
        else:
            print("   ⏸️  No notification")

        # Simulate time passing
        if i == 3:
            print("   (simulating 6 seconds passing...)")
            detector.last_prompt_time -= 6  # Fake time passage
