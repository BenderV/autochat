import unittest
from autochat.chat import Autochat
from autochat.model import Message


class MockTool:
    def __init__(self, name):
        self.name = name
        self.call_count = 0

    def __repr__(self):
        return f"MockTool(name={self.name}, call_count={self.call_count})"

    def increment(self):
        self.call_count += 1
        return self.call_count


class TestToolRepr(unittest.TestCase):
    def test_tool_repr_in_last_context(self):
        agent = Autochat(provider="openai")
        mock_tool = MockTool("TestTool")
        class_name = mock_tool.__class__.__name__
        tool_id = agent.add_tool(mock_tool)

        last_context = agent.last_context

        assert (
            f"### {class_name}-{tool_id}\nMockTool(name=TestTool, call_count=0)"
            in last_context
        )

        # Increment the mock tool's call count
        agent.functions[f"MockTool-{tool_id}__increment"]()

        last_context = agent.last_context
        assert (
            f"### {class_name}-{tool_id}\nMockTool(name=TestTool, call_count=1)"
            in last_context
        )

    def test_last_context_in_last_message(self):
        """
        We want to check that the last_context is in the last_message

        """
        agent = Autochat(provider="openai")
        mock_tool = MockTool("TestTool")
        class_name = mock_tool.__class__.__name__
        tool_id = agent.add_tool(mock_tool)

        # Mock the provider's fetch method
        def mock_fetch(**kwargs):
            # Get the last message after prepare_messages is called
            messages = agent.provider.prepare_messages(lambda x: x)
            last_message = messages[-1]

            # Verify the last_context is in the last message's content
            self.assertIn(
                f"### {class_name}-{tool_id}\nMockTool(name=TestTool, call_count=0)",
                last_message.parts[0].content,
            )
            return Message(role="assistant", content="Test response")

        agent.provider.fetch = mock_fetch
        agent.ask("Hello")


if __name__ == "__main__":
    unittest.main()
