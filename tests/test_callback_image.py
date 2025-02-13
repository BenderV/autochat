"""We want to be able to return an image from a function call.
"""

import pytest
from autochat import Autochat, APIProvider
from PIL import Image


def read_image():
    return Image.open("tests/images/mileage.jpg")


@pytest.mark.vcr
def test_anthropic_callback_image():
    agent = Autochat(
        provider=APIProvider.ANTHROPIC,
    )
    agent.add_function(read_image)

    user_query = "Hello, read the image and explain it"
    messages = []
    for message in agent.run_conversation(user_query):
        print(message.to_markdown())  # For debugging
        messages.append(message)


@pytest.mark.vcr
def test_openai_callback_image():
    agent = Autochat(
        provider=APIProvider.OPENAI,
    )
    agent.add_function(read_image)

    user_query = "Hello, read the image and explain it"
    messages = []
    for message in agent.run_conversation(user_query):
        print(message.to_markdown())  # For debugging
        messages.append(message)
