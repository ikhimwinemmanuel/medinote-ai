import json
from pathlib import Path
from judge.judge import evaluate_response
from langfuse.openai import OpenAI

client = OpenAI()

BASELINE_SYSTEM_PROMPT = """
You are provided with notes written by a doctor from a patient's visit.
Your job is to summarize the visit for the doctor and provide an email.
Reply with exactly three sections with the headings:
### Summary of visit for the doctor's records
### Next steps for the doctor
### Draft of email to patient in patient-friendly language
"""

def build_generation_prompt(case: dict) -> str:
    return f"""
Create the summary, next steps and draft email for:
Patient Name: {case['patient_name']}
Date of Visit: {case['date_of_visit']}
Notes:
{case['notes']}
"""

def generate_response(case: dict) -> str:
    user_prompt = build_generation_prompt(case)

    response = client.chat.completions.create(
        name="medinotes-baseline-evaluation",
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content

dataset_path = Path("evaluation/dataset/synthetic_consultations.json")

with open(dataset_path, "r", encoding="utf-8") as file:
    cases = json.load(file)

print(f"Loaded {len(cases)} evaluation case(s).")
print(f"First case: {cases[0]['id']}")

case = cases[0]
generated_output = generate_response(case)

print("\nGenerated response:\n")
print(generated_output)

source_context = f"""
Patient Name: {case['patient_name']}
Date of Visit: {case['date_of_visit']}
Notes:
{case['notes']}
"""

evaluation = evaluate_response(
    source_context,
    generated_output,
)

print("\nEvaluation:\n")
print(evaluation)