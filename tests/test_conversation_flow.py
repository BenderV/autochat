import pytest
from unittest.mock import patch, MagicMock
from autochat import Autochat, Message, APIProvider, Image
from PIL import Image as PILImage
import io


@pytest.fixture
def autochat():
    return Autochat(provider=APIProvider.OPENAI, model="gpt-4-turbo")


def test_conversation_flow(autochat):
    # Mock the OpenAI API call
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock the chat completion response
        mock_response = MagicMock()
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.function_call = {
            "name": "test_function",
            "arguments": '{"arg1": "value1"}',
        }
        mock_response.id = "response_id"
        mock_client.chat.completions.create.return_value = mock_response

        # Define a test function
        def test_function(arg1: str) -> str:
            """test"""
            return "Function result"

        autochat.add_function(test_function)

        # Start the conversation
        conversation = autochat.run_conversation("Hello")

        # Step 1: User message
        user_message = next(conversation)
        assert user_message.role == "user"
        assert user_message.content == "Hello"

        # # Step 2: Assistant function call
        assistant_message = next(conversation)
        assert assistant_message.role == "assistant"
        assert assistant_message.function_call["name"] == "test_function"

        # # Step 3: Function result
        # function_result = next(conversation)
        # assert function_result.role == "function"
        # assert function_result.content == "Function result"

        # # Mock the second API call (assistant's response to function result)
        # mock_response.choices[0].message.content = "Final response"
        # mock_response.choices[0].message.function_call = None

        # # Step 4: Assistant final message
        # final_message = next(conversation)
        # assert final_message.role == "assistant"
        # assert final_message.content == "Final response"


# def test_conversation_flow_with_image(autochat):
#     with patch("openai.OpenAI") as mock_openai:
#         mock_client = MagicMock()
#         mock_openai.return_value = mock_client

#         mock_response = MagicMock()
#         mock_response.choices[0].message.role = "assistant"
#         mock_response.choices[0].message.content = None
#         mock_response.choices[0].message.function_call = {
#             "name": "image_function",
#             "arguments": "{}",
#         }
#         mock_response.id = "response_id"
#         mock_client.chat.completions.create.return_value = mock_response

#         def image_function():
#             img = PILImage.new("RGB", (100, 100), color="red")
#             img_byte_arr = io.BytesIO()
#             img.save(img_byte_arr, format="PNG")
#             return img_byte_arr.getvalue()

#         autochat.add_function(image_function)

#         conversation = autochat.run_conversation("Generate an image")

#         user_message = next(conversation)
#         assert user_message.role == "user"
#         assert user_message.content == "Generate an image"

#         assistant_message = next(conversation)
#         assert assistant_message.role == "assistant"
#         assert assistant_message.function_call["name"] == "image_function"

#         function_result = next(conversation)
#         assert function_result.role == "function"
#         assert isinstance(function_result.image, Image)
#         assert function_result.content is None

#         mock_response.choices[0].message.content = "Image generated successfully"
#         mock_response.choices[0].message.function_call = None

#         final_message = next(conversation)
#         assert final_message.role == "assistant"
#         assert final_message.content == "Image generated successfully"
