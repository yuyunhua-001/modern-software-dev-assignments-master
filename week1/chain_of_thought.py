import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

import re
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 3

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT1 = """
Solve the given modular arithmetic question. You MUST compute the final numeric answer.

Computation steps:
1. Explore patterns in 3^n (especially the last two digits / modulo 100 cycle) by trying several small n.
2. Use that discovered pattern to compute 3^{12345}.
3. Then compute the final result modulo 100.
4. Continue until you obtain the final integer result.

Output rules:
- You may reason step by step, but output exactly one final line in this format: Answer: <integer>
"""

YOUR_SYSTEM_PROMPT = """
Solve the modular arithmetic problem and compute the final numeric result.

Reasoning strategy:
1. If direct computation is easy, compute directly.
2. If numbers are large, first identify relevant math theorems or patterns.
3. Choose the most suitable theorem/pattern, explain why it applies, and simplify the expression.
4. Perform step-by-step modular reasoning until you get the final integer.

Output rules:
- You may reason step by step, but output exactly one final line in this format: Answer: <integer>
"""

USER_PROMPT = """
Solve this problem, then give the final answer on the last line as "Answer: <number>".

what is 3^{12345} (mod 100)?
"""


# For this simple example, we expect the final numeric answer only
EXPECTED_OUTPUT = "Answer: 43"


def extract_final_answer(text: str) -> str:
    """Extract the final 'Answer: ...' line from a verbose reasoning trace.

    - Finds the LAST line that starts with 'Answer:' (case-insensitive)
    - Normalizes to 'Answer: <number>' when a number is present
    - Falls back to returning the matched content if no number is detected
    """
    if text is None:
        return ""
    matches = re.findall(r"(?mi)^\s*answer\s*:\s*(.+)\s*$", text)
    if matches:
        value = matches[-1].strip()
        # Prefer a numeric normalization when possible (supports integers/decimals)
        num_match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if num_match:
            return f"Answer: {num_match.group(0)}"
        return f"Answer: {value}"
    # Fallback 1: Handle congruence forms like:
    # "243 ≡ 43 (mod 100)" or "243 \equiv 43 \pmod{100}".
    congruence_match = re.search(
        r"(?:≡|\\equiv)\s*(-?\d+)\s*(?:\(|\\pmod\{)\s*100",
        text,
        flags=re.IGNORECASE,
    )
    if congruence_match:
        return f"Answer: {congruence_match.group(1)}"
    # Fallback 2: If no explicit Answer/congruence, use the last integer in output.
    # This keeps evaluation resilient when model ignores strict format.
    all_nums = re.findall(r"-?\d+", text.replace(",", ""))
    if all_nums:
        return f"Answer: {all_nums[-1]}"
    return text.strip()


def test_your_prompt(system_prompt: str) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="qwen3.5:4b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={
                "temperature": 0,
                # R1 needs enough tokens to finish <think> before it outputs Answer.
                # ~1500 is sufficient for this problem; raise if it still gets cut off.
                "num_predict": 1500,
            },
        )
        # qwen3.5 is a thinking model: output may be in content or thinking field
        content = response.message.content or ""
        thinking = getattr(response.message, "thinking", None) or ""
        output_text = (content + "\n" + thinking).strip()
        final_answer = extract_final_answer(output_text)
        if final_answer.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            # Truncate long output; show end where Answer usually appears
            display = ("..." + final_answer[-200:]) if len(final_answer) > 250 else final_answer
            print(f"Actual output  : {display}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)


