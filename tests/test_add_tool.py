from autochat.chat import Autochat


class DummyTool:
    def method1(self):
        pass

    def method2(self, param: str):
        pass

    def _private_method(self):
        pass


def test_add_tool():
    chat = Autochat()
    tool_id = chat.add_tool(DummyTool)

    # Check if the tool was added correctly
    assert tool_id in chat.tools
    assert isinstance(chat.tools[tool_id], DummyTool)

    # Check if all methods (excluding private) were added to functions_schema
    function_names = [f["name"] for f in chat.functions_schema]
    assert f"DummyTool-{tool_id}__method1" in function_names
    assert f"DummyTool-{tool_id}__method2" in function_names
    assert f"DummyTool-{tool_id}___private_method" not in function_names

    # Check if all functions (excluding private) were added correctly
    assert f"DummyTool-{tool_id}__method1" in chat.functions
    assert f"DummyTool-{tool_id}__method2" in chat.functions
    assert f"DummyTool-{tool_id}___private_method" not in chat.functions


def test_add_tool_with_custom_id():
    chat = Autochat()
    custom_id = "custom_tool_id"
    tool_id = chat.add_tool(DummyTool(), tool_id=custom_id)

    assert tool_id == custom_id
    assert custom_id in chat.tools
    assert isinstance(chat.tools[custom_id], DummyTool)


def test_add_tool_instance():
    chat = Autochat()
    tool_instance = DummyTool()
    tool_id = chat.add_tool(tool_instance)

    assert tool_id in chat.tools
    assert chat.tools[tool_id] is tool_instance

    # Check if all methods (excluding private) were added to functions_schema
    function_names = [f["name"] for f in chat.functions_schema]
    assert f"DummyTool-{tool_id}__method1" in function_names
    assert f"DummyTool-{tool_id}__method2" in function_names
    assert f"DummyTool-{tool_id}___private_method" not in function_names
