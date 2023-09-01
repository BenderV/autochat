import unittest

from autochat.utils import limit_data_size, parse_function


class TestLimitDataSizeUpdated(unittest.TestCase):
    def setUp(self):
        self.test_data_1 = [
            {"name": "Alice", "age": "25", "city": "New York"},
            {"name": "Bob", "age": "30", "city": "San Francisco"},
            {"name": "Charlie", "age": "35", "city": "Los Angeles"},
            {"name": "Daisy", "age": "40", "city": "Houston"},
        ]

        self.test_data_2 = [
            {"name": "Alice", "age": "25", "city": "New York"},
            {"name": "Bob", "age": "30", "city": "San Francisco"},
        ]

        self.test_data_3 = [
            {"name": "Alice", "age": "25", "city": "New York"},
            {"name": "B" * 50, "age": "30", "city": "San Francisco"},
        ]

    def test_small_character_limit(self):
        result = limit_data_size(self.test_data_2, character_limit=5)
        self.assertEqual(result, [{"name": "A", "age": "2", "city": "N"}])

    def test_larger_character_limit(self):
        result = limit_data_size(self.test_data_1, character_limit=150)
        expected = [
            {"name": "Alice", "age": "25", "city": "New York"},
            {"name": "Bob", "age": "30", "city": "San Francisco"},
            {"name": "Charlie", "age": "35", "city": "Los Angeles"},
            {"name": "Daisy", "age": "40", "city": "Houston"},
        ]
        self.assertEqual(result, expected)

    def test_very_long_single_field(self):
        result = limit_data_size(self.test_data_3, character_limit=80)
        expected = [{"name": "Alice", "age": "25", "city": "New York"}]
        self.assertEqual(result, expected)


plot_widget = """
> PLOT_WIDGET(
    name="Distribution of stations per city",
    outputType="Doughnut2d",
    sql="SELECT city, COUNT(*) FROM public.station GROUP BY city",
    params={"xAxisName": "City", "yAxisName":"Number of stations", "xKey":"city", "yKey":"count"}
)
"""


class TestParseFunction(unittest.TestCase):
    def test_no_arguments(self):
        text = """
        > FUNCTION()
        """
        # Except raises ValueError
        with self.assertRaises(ValueError):
            parse_function(text)

    def test_single_argument(self):
        text = """
        > FUNCTION(name="single argument")
        """
        result = parse_function(text)
        expected = {"name": "FUNCTION", "arguments": {"name": "single argument"}}
        self.assertEqual(result, expected)

    def test_multiple_arguments(self):
        text = """
        > FUNCTION(name="argument1", another="argument2")
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": {"name": "argument1", "another": "argument2"},
        }
        self.assertEqual(result, expected)

    def test_multiple_arguments_with_newlines(self):
        text = """
        > FUNCTION(
            name="argument1",
            another="argument2"
        )
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": {"name": "argument1", "another": "argument2"},
        }
        self.assertEqual(result, expected)

    def test_multiline_argument(self):
        text = """
        > FUNCTION(name="argument1", query=```SELECT column
        FROM table;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": {
                "name": "argument1",
                "query": "SELECT column        FROM table;        ",
            },
        }
        self.assertEqual(result, expected)

    def test_multiline_with_other_arguments(self):
        text = """
        > FUNCTION(name="argument1", description="describes something", query=```SELECT column
        FROM table;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": {
                "name": "argument1",
                "description": "describes something",
                "query": "SELECT column        FROM table;        ",
            },
        }
        self.assertEqual(result, expected)

    def test_parse_function(self):
        text = """
        > SQL_QUERY(name="installation_date column examples", query=```SELECT installation_date
        FROM public.station
        ORDER BY RANDOM()
        LIMIT 5;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "SQL_QUERY",
            "arguments": {
                "name": "installation_date column examples",
                "query": "SELECT installation_date        FROM public.station        ORDER BY RANDOM()        LIMIT 5;        ",
            },
        }
        self.assertEqual(result, expected)

    def test_parse_array(self):
        text = """
        > SQL_QUERY(name=["installation_date column examples", "another name"], test="one")
        """
        result = parse_function(text)
        expected = {
            "name": "SQL_QUERY",
            "arguments": {
                "name": ["installation_date column examples", "another name"],
                "test": "one",
            },
        }
        self.assertEqual(result, expected)

    def test_plot_widget(self):
        result = parse_function(plot_widget)
        expected = {
            "name": "PLOT_WIDGET",
            "arguments": {
                "name": "Distribution of stations per city",
                "outputType": "Doughnut2d",
                "sql": "SELECT city, COUNT(*) FROM public.station GROUP BY city",
                "params": {
                    "xAxisName": "City",
                    "yAxisName": "Number of stations",
                    "xKey": "city",
                    "yKey": "count",
                },
            },
        }
        self.assertDictEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
