import json
import google.generativeai as genai
from django.conf import settings


def _get_model():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-3-flash-preview")


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def generate_first_question(resume, experience, difficulty, topic, role):
    topic_line = (
        f"Topic: {topic}" if topic
        else f"Topic: AI's choice — pick topics relevant to a {role} role"
    )

    prompt = f"""You are a professional technical interviewer conducting a real interview
for the role of {role}.

Candidate Resume:
{resume[:3000]}

Target Role:      {role}
Experience Level: {experience}
Difficulty:       {difficulty}
{topic_line}

Instructions:
- Ask ONLY ONE interview question, relevant to the {role} role
- Make it realistic — the kind of question actually asked for this role
- Match the difficulty strictly
- Use the resume context to personalise if possible
- Do NOT include any preamble — just the question itself

Respond with ONLY the question text. Nothing else."""

    model = _get_model()
    response = model.generate_content(prompt)
    return response.text.strip()


def get_feedback_and_next(resume, experience, difficulty, topic, role,
                          history, current_question, candidate_answer):
    topic_line = (
        f"Topic: {topic}" if topic
        else f"Topic: not fixed — vary topics relevant to a {role} role"
    )

    history_text = ""
    if history:
        pairs = history[-5:]
        history_text = "\n".join(
            f"Q{i+1}: {p['question']}\nA{i+1}: {p['answer']}"
            for i, p in enumerate(pairs)
        )

    prompt = f"""You are a professional technical interviewer evaluating a candidate's answer.
The candidate is interviewing for the role of {role}.

Candidate Resume:
{resume[:2000]}

Target Role:      {role}
Experience Level: {experience}
Difficulty:       {difficulty}
{topic_line}

Previous Q&A History:
{history_text or "None (this is the first question)"}

Current Question:
{current_question}

Candidate's Answer:
{candidate_answer}

Your Tasks:
1. Evaluate the answer honestly but supportively.
2. Generate the NEXT interview question for a {role} candidate:
   - If answer was weak → go deeper on the same concept
   - If answer was strong → move to a new topic relevant to {role}
   - Always respect the difficulty level
   - If topic is fixed → stay within it
   - If topic is free → vary topics naturally for a {role} interview

Respond ONLY with a valid JSON object (no markdown fences, no extra text):
{{
  "correctness": "Was the answer correct? Explain briefly.",
  "missing_points": "Key points the candidate missed.",
  "improvements": "Specific suggestions to improve the answer.",
  "sample_answer": "A concise ideal answer.",
  "encouragement": "One encouraging sentence.",
  "next_question": "The next interview question for a {role} role (just the question text)."
}}"""

    model = _get_model()
    response = model.generate_content(prompt)
    raw = _clean_json(response.text)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "correctness":    "Could not parse AI response. Please try again.",
            "missing_points": "—",
            "improvements":   "—",
            "sample_answer":  "—",
            "encouragement":  "Keep going, you're doing great!",
            "next_question":  current_question,
        }