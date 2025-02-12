import anthropic
from autochat.providers.base_provider import BaseProvider
from autochat.model import Message, MessagePart
from autochat.base import AutochatBase


def part_to_anthropic_dict(part: MessagePart) -> dict:
    if part.type == "text":
        return {
            "type": "text",
            "text": part.content,
        }
    elif part.type == "image":
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": part.image.format,
                "data": part.image.to_base64(),
            },
        }
    elif part.type == "function_call":
        return {
            "type": "tool_use",
            "id": part.function_call_id,
            "name": part.function_call["name"],
            "input": part.function_call["arguments"],
        }
    elif part.type == "function_result_image":
        return {
            "type": "tool_result",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": part.image.format,
                        "data": part.image.to_base64(),
                    },
                }
            ],
            "tool_use_id": part.function_call_id,
        }
    elif part.type == "function_result":
        return {
            "type": "tool_result",
            "tool_use_id": part.function_call_id,
            "content": part.content,
        }
    raise ValueError(f"Unknown part type: {part.type}")


def message_to_anthropic_dict(message: Message) -> dict:
    res = {
        "role": message.role if message.role in ["user", "assistant"] else "user",
        "content": [],
    }

    for part in message.parts:
        res["content"].append(part_to_anthropic_dict(part))

    return res


class AnthropicProvider(BaseProvider):
    def __init__(self, chat: AutochatBase, model: str):
        self.model = model
        self.client = anthropic.Anthropic(
            default_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
        )
        self.chat = chat

    def fetch(self, **kwargs):
        def add_empty_function_result(messages):
            """
            Ajustement Anthropic pour fusionner ou insérer la « function_result » :

            - Premier cas : message `role="function"` suivi d’un `role="user"`.
            On transforme ce message 'function' en un part de type 'tool_result'
            inséré au début du message utilisateur suivant.

            - Second cas (inchangé) : message `role="assistant"` avec un `function_call`,
            suivi d’un message non-`function`. On insère un message vide `role="function"`.
            """
            for i in range(len(messages) - 1, 0, -1):
                if (
                    messages[i - 1].role == "assistant"
                    and messages[i - 1].function_call
                    and not messages[i].role == "function"
                ):
                    # Insert an empty function result
                    messages.insert(
                        i,
                        Message(
                            role="function",
                            name=messages[i - 1].function_call["name"],
                            content="",
                            function_call_id=messages[i - 1].function_call_id,
                        ),
                    )

        messages = self.prepare_messages(
            transform_function=lambda m: message_to_anthropic_dict(m),
            transform_list_function=add_empty_function_result,
        )

        if self.chat.instruction:
            system = self.chat.instruction
        else:
            system = None

        def merge_messages(messages):
            """
            When two messages are in the same role, we merge the following message into the previous.
            {
                "role": "user",
                "content": [
                    {
                    "type": "tool_result",
                    "tool_use_id": "example_19",
                    "content": ""
                    }
                ]
            },
            {
                "role": "user",
                "content": "Plot distribution of stations per city"
            }
            """
            merged_messages = []
            for message in messages:
                if merged_messages and merged_messages[-1]["role"] == message["role"]:
                    if isinstance(merged_messages[-1]["content"], str):
                        merged_messages[-1]["content"].append(
                            {
                                "type": "text",
                                "text": merged_messages[-1]["content"],
                            }
                        )
                    elif isinstance(merged_messages[-1]["content"], list):
                        merged_messages[-1]["content"].extend(message["content"])
                    else:
                        raise ValueError(
                            f"Invalid content type: {type(merged_messages[-1]['content'])}"
                        )
                else:
                    merged_messages.append(message)
            return merged_messages

        messages = merge_messages(messages)

        # Need to map field "parameters" to "input_schema"
        tools = [
            {
                "name": s["name"],
                "description": s["description"],
                "input_schema": s["parameters"],
            }
            for s in self.chat.functions_schema
        ]
        # Add description to the function is their description is empty
        for tool in tools:
            if not tool["description"]:
                tool["description"] = "No description provided"

        # === Add cache_controls ===
        # Messages: Find the last message with an index multiple of 10
        last_message_index = next(
            (i for i in reversed(range(len(messages))) if i % 10 == 0),
            None,
        )

        if last_message_index is not None:
            if isinstance(messages[last_message_index]["content"], list) and isinstance(
                messages[last_message_index]["content"][-1], dict
            ):
                messages[last_message_index]["content"][-1]["cache_control"] = {
                    "type": "ephemeral"
                }
            elif isinstance(messages[last_message_index]["content"], str):
                messages[last_message_index]["content"] = [
                    {
                        "type": "text",
                        "text": messages[last_message_index]["content"],
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
        # Tools: Add cache_control to the last tool function
        if tools:
            tools[-1]["cache_control"] = {"type": "ephemeral"}

        # System: add cache_control to the system message
        if system is not None:
            system = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        # === End of cache_control ===

        if system is not None:
            kwargs["system"] = system

        res = self.client.messages.create(
            model=self.model,
            messages=messages,
            tools=tools,
            max_tokens=2000,
            **kwargs,
        )
        res_dict = res.to_dict()
        return Message.from_anthropic_dict(
            role=res_dict["role"],
            content=res_dict["content"],
        )
