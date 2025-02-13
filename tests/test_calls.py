import pytest
from autochat import Autochat, APIProvider

# Our "book" data
BOOKS = {
    "The Great Gatsby": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "To Kill a Mockingbird": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "1984": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
}


def list_books():
    return list(BOOKS.keys())


def read_book(book_name: str):
    return BOOKS[book_name]


@pytest.mark.vcr
def test_anthropic_read_book():
    agent = Autochat(
        "You are a helpful assistant that can read books.",
        #
        provider=APIProvider.ANTHROPIC,
    )
    agent.add_function(list_books)
    agent.add_function(read_book)

    user_query = "Hello, read book 'the great gatsby'"
    messages = []
    for message in agent.run_conversation(user_query):
        print(message.to_markdown())  # For debugging
        messages.append(message)


@pytest.mark.vcr
def test_openai_read_book():
    agent = Autochat(
        "You are a helpful assistant that can read books.",
        model="gpt-4o",
        provider=APIProvider.OPENAI,
    )
    agent.add_function(list_books)
    agent.add_function(read_book)

    user_query = "Hello, read book 'the great gatsby'"
    messages = []
    for message in agent.run_conversation(user_query):
        print(message.to_markdown())  # For debugging
        messages.append(message)
