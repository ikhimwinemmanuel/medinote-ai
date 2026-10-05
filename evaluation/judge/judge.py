from pydantic import BaseModel
from langfuse.openai import OpenAI 


class EvaluationResult(BaseModel):

    groundedness: int
    patient_clarity: int
    unsupported_claims: int
    completeness: int
    instruction_following: int
    feedback: str


    

JUDGE_SYSTEM_PROMPT = """
You are evaluating the output of MediNotes AI against the original consultation notes.

Score the response using these criteria:

Groundedness: 1-5
How well the generated response is supported by the consultation notes.

Completeness: 1-5
Whether important information from the consultation notes is included.

Instruction following: 1-5
Whether the response follows the required three-section structure.

Patient clarity: 1-5
Whether the patient-facing email is clear and easy to understand.

Unsupported claims:
Count how many claims appear in the generated response that are not supported by the consultation notes.

Do not reward information simply because it sounds medically reasonable.
If it is not supported by the source consultation notes, treat it as unsupported.

Provide a short explanation in the feedback field.
"""

def build_judge_prompt(original_notes: str, generated_output: str) -> str:
    return f"""
Original consultation notes:
{original_notes}

MediNotes generated response:
{generated_output}
"""

def evaluate_response(
    original_notes: str,
    generated_output: str,
) -> EvaluationResult:
    client = OpenAI()
    judge_prompt = build_judge_prompt(original_notes, generated_output)

    completion = client.chat.completions.parse(
    name="medinotes-judge",
    model="gpt-6.1-sol",
    messages=[
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": judge_prompt},
    ],
    response_format=EvaluationResult,
)

    result = completion.choices[0].message.parsed

    if result is None:
        raise ValueError("Judge did not return a valid evaluation.")

    return result

