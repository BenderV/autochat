import ast
import csv
from io import StringIO


def limit_data_size(
    data: list[dict[str, str]], character_limit: int = 10000
) -> list[dict[str, str]]:
    # Helper function to get total character count for a given row
    def get_row_char_count(row: dict[str, str]) -> int:
        return (
            sum(len(str(value)) + len(str(key)) for key, value in row.items())
            + len(row)
            - 1
        )

    # Helper function to limit the characters per field in a row
    def limit_row_chars(
        row: dict[str, str], char_limit_per_field: int
    ) -> dict[str, str]:
        return {key: str(value)[:char_limit_per_field] for key, value in row.items()}

    # Initialize the resulting data list and the character counter
    result_data = []
    total_char_count = 0

    for row in data:
        # Calculate the character count for the current row
        row_char_count = get_row_char_count(row)

        # If adding this row will exceed the limit
        if total_char_count + row_char_count > character_limit:
            # If this is the only row we are processing, then limit characters per field
            if len(result_data) == 0:
                avg_chars_per_field = (character_limit - total_char_count) // len(row)
                if avg_chars_per_field < 1:
                    return "Error: Too many fields to display data within the character limit."
                limited_row = limit_row_chars(row, avg_chars_per_field)
                result_data.append(limited_row)
            break

        # Otherwise, add this row to the result and update the total character count
        result_data.append(row)
        total_char_count += row_char_count

    return result_data


def csv_dumps(data: list[dict]) -> str:
    # Dumps to CSV, with header row
    if not data:
        return "[]"

    limited_data = limit_data_size(data, character_limit=500)
    header = list(data[0].keys())
    with StringIO() as output:
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writeheader()
        writer.writerows(limited_data)
        output = output.getvalue().strip()
        output.replace("\r\n", "\n").replace("\r", "\n")

    if len(limited_data) < len(data):
        output += f"\n\n... {len((limited_data))} of {len(data)} rows displayed."
    return output


def parse_function(text: str) -> dict:
    # Cleaning the text
    lines = text.strip().split("\n")
    text = "".join(
        line[2:] if line.startswith(">") else line for line in lines
    )  # remove the leading ">"

    # Replacing the multiline string delimiters
    parts = text.split("```")
    for i in range(1, len(parts), 2):
        parts[i] = f"'''{parts[i]}'''"
    text = "".join(parts)

    # Parsing the text using ast
    parsed = ast.parse(text).body[0].value

    # Check if it's a valid function call
    if not isinstance(parsed, ast.Call):
        raise ValueError("The text does not contain a valid function call.")

    # Extracting the function name
    function_name = parsed.func.id

    # Extracting the arguments
    arguments = {}
    for keyword in parsed.keywords:
        if isinstance(keyword.value, ast.Str):
            value = keyword.value.s
            arguments[keyword.arg] = value
        elif isinstance(keyword.value, ast.List):
            arguments[keyword.arg] = [el.s for el in keyword.value.elts]
        elif isinstance(keyword.value, ast.Dict):
            dict_values = {}
            for k, v in zip(keyword.value.keys, keyword.value.values):
                if isinstance(v, ast.Str):
                    dict_values[k.s] = v.s
            arguments[keyword.arg] = dict_values

    if not arguments:
        raise ValueError("The function call does not contain any arguments.")

    return {"name": function_name, "arguments": arguments}
