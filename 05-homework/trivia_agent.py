import html
import requests
from pydantic_ai import Agent, RunUsage
from pydantic_ai.messages import FunctionToolCallEvent

import dotenv
dotenv.load_dotenv()
dotenv.load_dotenv("../documentation-agent/.env")

import logfire

# Reads LOGFIRE_TOKEN (a write token) from the environment / .env
logfire.configure(service_name="trivia-agent")
logfire.instrument_pydantic_ai()

BASE_URL = "https://opentdb.com"


class TriviaTools:
    """Fetches trivia categories and questions from the Open Trivia DB API."""

    def get_categories(self) -> list[dict]:
        """
        List the available trivia categories.

        Returns:
            list[dict]: categories, each with an 'id' and a 'name'.
        """
        response = requests.get(f"{BASE_URL}/api_category.php")
        response.raise_for_status()
        return response.json()["trivia_categories"]

    def get_questions(
        self,
        amount: int = 5,
        category: int | None = None,
        difficulty: str | None = None,
    ) -> list[dict]:
        """
        Fetch multiple-choice trivia questions.

        Args:
            amount (int): number of questions (1-50).
            category (int): optional category id from get_categories.
            difficulty (str): optional, one of 'easy', 'medium', 'hard'.

        Returns:
            list[dict]: questions with 'question', 'correct_answer' and 'incorrect_answers'.
        """
        params = {"amount": amount, "type": "multiple"}
        if category is not None:
            params["category"] = category
        if difficulty is not None:
            params["difficulty"] = difficulty

        response = requests.get(f"{BASE_URL}/api.php", params=params)
        response.raise_for_status()
        results = response.json()["results"]

        for r in results:
            r["question"] = html.unescape(r["question"])
            r["correct_answer"] = html.unescape(r["correct_answer"])
            r["incorrect_answers"] = [html.unescape(a) for a in r["incorrect_answers"]]
        return results


instructions = """You are a trivia quizmaster. When asked to play trivia:
1. Use the available tools to fetch trivia questions
2. Ask the player one question at a time with multiple choice options
3. Wait for their answer before moving to the next question
4. When the player answers, explain why the correct answer is correct - add interesting context and facts
5. After all questions, give the final score
"""

trivia_tools = TriviaTools()

agent = Agent(
    'openai:gpt-4o-mini',
    name='agent',
    tools=[trivia_tools.get_categories, trivia_tools.get_questions],
    instructions=instructions,
)


def run(prompt):
    message_history = []
    total = RunUsage()

    while True:
        result = agent.run_sync(prompt, message_history=message_history)
        print(result.output)
        message_history = result.all_messages()
        total += result.usage

        prompt = input("You (write 'stop' to stop): ")
        if not prompt or prompt.lower().strip() == 'stop':
            break

    print(f"\nSESSION USAGE: input={total.input_tokens} output={total.output_tokens} requests={total.requests}")


if __name__ == "__main__":
    with logfire.span('trivia_session'):
        run("Let's play 5 easy questions from Science & Nature")
