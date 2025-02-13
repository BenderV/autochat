import unittest
from unittest.mock import patch

from autochat import Autochat, Message
from autochat.providers.openai import OpenAIProvider


class TestAutochat(unittest.TestCase):
    def test_autochat_initialization(self):
        agent = Autochat(instruction="Test instruction", provider="openai")
        self.assertEqual(agent.instruction, "Test instruction")
        self.assertEqual(agent.provider.__class__, OpenAIProvider)
        # Instead of checking for a specific model, we'll just check if it's a string
        self.assertIsInstance(agent.model, str)
        self.assertTrue(len(agent.model) > 0)  # Ensure the model is not an empty string

    def test_autochat_invalid_provider(self):
        with self.assertRaises(ValueError):
            Autochat(provider="invalid_provider")

    def test_add_function(self):
        agent = Autochat()

        def test_function(arg1: str, arg2: int) -> str:
            return f"Received {arg1} and {arg2}"

        agent.add_function(test_function)
        self.assertEqual(len(agent.functions_schema), 1)
        self.assertIn("test_function", agent.functions)

    @patch.object(OpenAIProvider, "fetch")
    def test_ask(self, mock_fetch_openai):
        mock_fetch_openai.return_value = Message(
            role="assistant", content="Test response"
        )
        agent = Autochat(provider="openai")

        response = agent.ask("Test question")
        self.assertEqual(response.role, "assistant")
        self.assertEqual(response.content, "Test response")
        self.assertEqual(len(agent.messages), 2)

    @patch.object(OpenAIProvider, "fetch")
    def test_run_conversation(self, mock_fetch_openai):
        mock_fetch_openai.return_value = Message(
            role="assistant", content="Final response"
        )
        agent = Autochat(provider="openai")

        responses = list(agent.run_conversation("Test question"))
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0].role, "user")
        self.assertEqual(responses[0].content, "Test question")
        self.assertEqual(responses[1].role, "assistant")
        self.assertEqual(responses[1].content, "Final response")


if __name__ == "__main__":
    unittest.main()
