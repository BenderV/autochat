import json
import unittest
from unittest.mock import MagicMock, patch

from anthropic.types import ContentBlock
from anthropic.types import Message as AnthropicMessage

from autochat import APIProvider, Autochat, Message


class TestAnthropic(unittest.TestCase):
    def setUp(self):
        self.mock_anthropic_client = MagicMock()

    def test_transform_conversation_anthropic(self):
        chat = Autochat(instruction="Test instruction", provider=APIProvider.ANTHROPIC)
        chat.messages = [
            Message(
                role="function",
                name="SUBMIT",
                content="",
                function_call_id="example_16",
            ),
            Message(role="user", content="Plot distribution of stations per city"),
        ]

        expected_output = [
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "example_16", "content": ""},
                    {
                        "type": "text",
                        "text": "Plot distribution of stations per city",
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
            }
        ]
        chat.client = self.mock_anthropic_client

        class FakeAnthropicMessage:
            def __init__(self, role, content):
                self.role = role
                self.content = content

            def to_dict(self):
                return {
                    "role": self.role,
                    "content": self.content,
                }

        return_value = FakeAnthropicMessage(
            role="assistant",
            content="test",
        )

        with patch.object(
            chat.client.messages, "create", return_value=return_value
        ) as mock_call:
            chat.fetch_anthropic()
            self.mock_anthropic_client.messages.create.assert_called_once()
            call_args = self.mock_anthropic_client.messages.create.call_args
            actual_messages = call_args.kwargs["messages"]

            self.assertEqual(actual_messages, expected_output)


if __name__ == "__main__":
    unittest.main()
