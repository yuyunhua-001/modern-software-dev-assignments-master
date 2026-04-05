import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 3

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """
Examples (Input -> Output):
hello -> olleh
system -> metsys
abc123 -> 321cba
"""

USER_PROMPT = """
Reverse the order of letters in the following word. ONLY output the reversed word, NO other text:
httpstatusp
"""
EXPECTED_OUTPUT = "psutatsptth"


def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"\nRunning test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="deepseek-r1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.1},
        )
        output_text = response.message.content.strip().split('\n')[-1].strip()
        if output_text == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected: {EXPECTED_OUTPUT}")
            print(f"Actual  : {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)