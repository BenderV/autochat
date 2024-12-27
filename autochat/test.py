import unittest
from unittest.mock import patch

from autochat import APIProvider, Autochat, ContextLengthExceededError, Message


class TestAutochat(unittest.TestCase):
    def test_autochat_initialization(self):
        chat = Autochat(instruction="Test instruction", provider="openai")
        self.assertEqual(chat.instruction, "Test instruction")
        self.assertEqual(chat.provider, APIProvider.OPENAI)
        self.assertEqual(chat.model, "gpt-4o")

    def test_autochat_invalid_provider(self):
        with self.assertRaises(ValueError):
            Autochat(provider="invalid_provider")

    def test_add_function(self):
        chat = Autochat()

        def test_function(arg1: str, arg2: int) -> str:
            return f"Received {arg1} and {arg2}"

        chat.add_function(test_function)
        self.assertEqual(len(chat.functions_schema), 1)
        self.assertIn("test_function", chat.functions)

    @patch.object(Autochat, "fetch_openai")
    def test_ask(self, mock_fetch_openai):
        mock_fetch_openai.return_value = Message(
            role="assistant", content="Test response"
        )
        chat = Autochat(provider="openai")

        response = chat.ask("Test question")
        self.assertEqual(response.role, "assistant")
        self.assertEqual(response.content, "Test response")
        self.assertEqual(len(chat.messages), 2)

    @patch.object(Autochat, "fetch_openai")
    def test_run_conversation(self, mock_fetch_openai):
        mock_fetch_openai.return_value = Message(
            role="assistant", content="Final response"
        )
        chat = Autochat(provider="openai")

        responses = list(chat.run_conversation("Test question"))
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0].role, "user")
        self.assertEqual(responses[0].content, "Test question")
        self.assertEqual(responses[1].role, "assistant")
        self.assertEqual(responses[1].content, "Final response")

    @patch.object(Autochat, "fetch_openai")
    def test_context_length_exceeded(self, mock_fetch_openai):
        mock_fetch_openai.side_effect = ContextLengthExceededError(
            "Context length exceeded"
        )
        chat = Autochat(provider="openai")

        with self.assertRaises(ContextLengthExceededError):
            chat.ask("Test question")


if __name__ == "__main__":
    unittest.main()
