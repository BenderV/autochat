import os

import pytest
from PIL import Image

from autochat import APIProvider, Autochat, Message

img_path = os.path.join(os.path.dirname(__file__), "images", "mileage.jpg")


def report_mileage(km: int):
    """Report the mileage of the car (in km)"""
    print(f"The car has {km} km on the odometer.")
    return f"The car has {km} km on the odometer."


@pytest.mark.vcr
def test_openai_read_image():
    agent = Autochat(provider=APIProvider.OPENAI)
    agent.add_function(report_mileage)

    image = Image.open(img_path)
    message = Message(
        role="user",
        content="report the  mileage of the car",
        image=image,
    )
    response = agent.ask(
        message,
        # TODO: support tools in openai to be able to enforce the tool call
        # tool_choice={"type": "function", "function": {"name": "report_mileage"}},
    )
    print(response.to_markdown())
    # assert response.function_call["name"] == "report_mileage"
    # assert isinstance(response.function_call["arguments"].get("km"), int)


@pytest.mark.vcr
def test_anthropic_read_image():
    agent = Autochat(provider=APIProvider.ANTHROPIC)
    agent.add_function(report_mileage)

    image = Image.open(img_path)
    message = Message(
        role="user",
        content="report the  mileage of the car",
        image=image,
    )
    response = agent.ask(
        message, tool_choice={"type": "tool", "name": "report_mileage"}
    )
    assert response.function_call["name"] == "report_mileage"
    assert isinstance(response.function_call["arguments"].get("km"), int)
