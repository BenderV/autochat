from autochat import Autochat, Message

from PIL import Image
import sys
import os
import argparse

sys.path.append("..")

parser = argparse.ArgumentParser(description="Describe an image using AI")
parser.add_argument(
    "--provider",
    type=str,
    default="anthropic",
    help="AI provider (e.g., 'anthropic', 'openai')",
)
args = parser.parse_args()

agent = Autochat(provider=args.provider)

current_dir = os.path.dirname(os.path.abspath(__file__))
image = Image.open(os.path.join(current_dir, "image.jpg"))
message = Message(role="user", content="describe the image", image=image)
response = agent.ask(message)
print(response)
