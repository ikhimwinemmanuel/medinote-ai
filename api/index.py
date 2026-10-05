import os
from fastapi import FastAPI, Depends  # type: ignore
from fastapi.responses import StreamingResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials  # type: ignore
from langfuse.openai import OpenAI  # type: ignore
from langfuse import get_client # type: ignore

app = FastAPI()

clerk_config = ClerkConfig(
    jwks_url=os.getenv("CLERK_JWKS_URL")
)

clerk_guard = ClerkHTTPBearer(clerk_config)


class Visit(BaseModel):
    patient_name: str
    date_of_visit: str
    notes: str


system_prompt = """
You are provided with notes written by a doctor from a patient's visit.

Use only information explicitly provided in the consultation notes.
Do not add diagnoses, treatments, medications, tests, follow-up actions, warnings, or recommendations that are not stated in the notes.

Reply with exactly three sections:

### Summary of visit for the doctor's records
Summarize the information provided in the consultation notes.

### Next steps for the doctor
Include only follow-up actions or next steps explicitly stated in the consultation notes.

### Draft of email to patient in patient-friendly language
Explain the consultation and documented follow-up in clear language without adding new medical advice.
"""


def user_prompt_for(visit: Visit) -> str:
    return f"""Create the summary, next steps and draft email for:
Patient Name: {visit.patient_name}
Date of Visit: {visit.date_of_visit}
Notes:
{visit.notes}"""


@app.post("/api")
def consultation_summary(
    visit: Visit,
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard),
):
    user_id = creds.decoded["sub"]

    client = OpenAI()
    langfuse = get_client()

    user_prompt = user_prompt_for(visit)

    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    stream = client.chat.completions.create(
        name="medinotes-consultation",
        model="gpt-5-nano",
        messages=prompt,
        stream=True,
    )

    def event_stream():
        try:
            for chunk in stream:
                text = chunk.choices[0].delta.content


                if text:
                    lines = text.split("\n")

                    for line in lines[:-1]:
                        yield f"data: {line}\n\n"
                        yield "data:  \n"

                    yield f"data: {lines[-1]}\n\n"
    
        finally:
            langfuse.flush()
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )