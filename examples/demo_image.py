from PIL import Image
import sys
import argparse

sys.path.append("..")
from autochat import Autochat, Message

parser = argparse.ArgumentParser(description="Describe an image using AI")
parser.add_argument(
    "--provider",
    type=str,
    default="anthropic",
    help="AI provider (e.g., 'anthropic', 'openai')",
)
args = parser.parse_args()

ai = Autochat(provider=args.provider)

image = Image.open("./image.jpg")
message = Message(role="user", content="describe the image", image=image)
response = ai.ask(message)
print(response)
