from PIL import Image as PILImage
import sys

sys.path.append("..")
from autochat import Autochat, Message, Image

ai = Autochat(provider="openai")

image = Image(PILImage.open("./image.jpg"))
response = ai.ask(Message(role="user", content="describe the image", image=image))
print(response)
