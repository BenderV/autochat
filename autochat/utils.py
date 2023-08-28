import csv
import re
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


def parse_function(text):
    # Match function name and its optional arguments
    match = re.search(r"\s*(\w+)(?:\(([^>]+)\))?\s*$", text, re.DOTALL)
    if not match:
        raise ValueError(f"Invalid function call: {text}")

    function_name = match.group(1)
    arguments_text = match.group(2) if match.group(2) else ""

    # Split the arguments into key-value pairs
    arg_pairs = re.findall(r'(\w+)="([^"]+)"', arguments_text)
    additional_arg = re.search(r"(\w+)=```(.*?)```", arguments_text, re.DOTALL)
    if additional_arg:
        # Remove extra indentation from multi-line arguments
        content = "\n".join(
            [
                line.strip()
                for line in additional_arg.group(2).splitlines()
                if line.strip()
            ]
        )
        arg_pairs.append((additional_arg.group(1), content))

    arguments = {key: value for key, value in arg_pairs}

    result = {"name": function_name, "arguments": arguments}
    return result
