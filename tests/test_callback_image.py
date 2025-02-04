"""We want to be able to return an image from a function call.
"""

import pytest
from autochat import Autochat, APIProvider
from PIL import Image


def read_image():
    return Image.open("tests/images/mileage.jpg")


@pytest.mark.vcr
def test_anthropic_callback_image():
    chat = Autochat(
        provider=APIProvider.ANTHROPIC,
    )
    chat.add_function(read_image)

    user_query = "Hello, read the image and explain it"
    messages = []
    for message in chat.run_conversation(user_query):
        print(message.to_markdown())  # For debugging
        messages.append(message)


@pytest.mark.vcr
def test_openai_callback_image():
    chat = Autochat(
        provider=APIProvider.OPENAI,
    )
    chat.add_function(read_image)

    user_query = "Hello, read the image and explain it"
    messages = []
    for message in chat.run_conversation(user_query):
        print(message.to_markdown())  # For debugging
        messages.append(message)
