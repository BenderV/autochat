import pytest
from PIL import Image

from autochat import Autochat, Message, APIProvider


def report_mileage(km: int):
    """Report the mileage of the car (in km)"""
    print(f"The car has {km} km on the odometer.")
    return f"The car has {km} km on the odometer."


@pytest.mark.vcr
def test_openai_read_image():
    chat = Autochat(provider=APIProvider.OPENAI)
    chat.add_function(report_mileage)

    image = Image.open("tests/images/mileage.jpg")
    message = Message(
        role="user",
        content="report the  mileage of the car",
        image=image,
    )
    response = chat.ask(
        message,
        # TODO: support tools in openai to be able to enforce the tool call
        # tool_choice={"type": "function", "function": {"name": "report_mileage"}},
    )
    print(response.to_markdown())
    # assert response.function_call["name"] == "report_mileage"
    # assert isinstance(response.function_call["arguments"].get("km"), int)


@pytest.mark.vcr
def test_anthropic_read_image():
    chat = Autochat(provider=APIProvider.ANTHROPIC)
    chat.add_function(report_mileage)

    image = Image.open("tests/images/mileage.jpg")
    message = Message(
        role="user",
        content="report the  mileage of the car",
        image=image,
    )
    response = chat.ask(message, tool_choice={"type": "tool", "name": "report_mileage"})
    assert response.function_call["name"] == "report_mileage"
    assert isinstance(response.function_call["arguments"].get("km"), int)
