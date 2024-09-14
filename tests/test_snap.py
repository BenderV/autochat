from unittest.mock import patch
import pytest
from autochat import Autochat, APIProvider


class TestAutochat:
    @pytest.mark.snapshot
    def test_fetch_openai(self, snapshot):
        with patch("openai.OpenAI") as mock_openai:
            # Setup the mock response
            mock_response = (
                mock_openai.return_value.chat.completions.create.return_value
            )
            mock_response.choices[0].message.role = "assistant"
            mock_response.choices[0].message.content = "Mocked response content"
            mock_response.choices[0].message.function_call = None
            mock_response.id = "mocked_response_id"

            # Create an instance of Autochat
            autochat = Autochat(provider=APIProvider.OPENAI)

            # Call the method
            result = autochat.ask("Hello, how are you?")

            print(result)
            # Assert that the result matches the snapshot
            snapshot.assert_match(result.to_openai_dict())
