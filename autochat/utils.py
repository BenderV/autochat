import csv
import json
import re
from io import StringIO


def csv_dumps(data):
    # Dumps to CSV, with header row
    if not data:
        return
    header = list(data[0].keys())
    with StringIO() as output:
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)
        output = output.getvalue().strip()
        return output.replace("\r\n", "\n").replace("\r", "\n")


def parse_function(text):
    """
    > parse_function("func1(key1=`value1`)")
    {'name': 'func1', 'arguments': '{"key1": "value1"}'}

    > parse_function("func()")
    {'name': 'func', 'arguments': '{}'}

    """
    function_pattern = r"(\w+)\((\w+)=([`\"].*?[`\"])\)"
    matches = re.finditer(function_pattern, text, re.DOTALL)

    parsed_functions = []

    for match in matches:
        function_name = match.group(1).strip()
        param_key = match.group(2).strip()
        param_value = match.group(3).strip('`"')

        arguments = {param_key: param_value}
        parsed_function = {"name": function_name, "arguments": arguments}
        parsed_functions.append(parsed_function)

    return parsed_functions[0]
