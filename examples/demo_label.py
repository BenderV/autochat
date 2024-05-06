import json
import sys

sys.path.append("..")

from autochat import ChatGPT, Message


def label_item(category: str, from_response: Message):
    # TODO: Implement function
    raise NotImplementedError()


with open("./function_label.json") as f:
    FUNCTION_LABEL_ITEM = json.load(f)

classifierGPT = ChatGPT.from_template("./classify_template.txt")
classifierGPT.add_function(label_item, FUNCTION_LABEL_ITEM)

text = "The new iPhone is out"
for message in classifierGPT.run_conversation(text):
    print(message.to_markdown())
