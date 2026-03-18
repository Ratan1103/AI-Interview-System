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


# 🔥 COMMON RULES FOR QUESTION QUALITY
QUESTION_RULES = """
Question Rules:
- Ask ONLY ONE question
- Focus on ONLY ONE concept (no multi-part questions)
- Keep the question SHORT (max 25 words, 2–3 lines max)
- Make it clear and easy to understand
- Avoid long scenario-based or multi-layered questions

Difficulty Rules:
- Easy → basic definitions or simple concepts
- Medium → one concept + practical reasoning (NO system design)
- Hard → may include system design or deeper reasoning
"""


# 🚀 FIRST QUESTION
def generate_first_question(resume, experience, difficulty, topic, role):
    topic_line = (
        f"Topic: {topic}"
        if topic
        else f"Topic: Choose relevant topics for a {role} role"
    )

    prompt = f"""You are a professional technical interviewer.

The candidate is applying for: {role}

Candidate Resume:
{resume[:2000]}

Experience Level: {experience}
Difficulty Level: {difficulty}
{topic_line}

{QUESTION_RULES}

Instructions:
- Ask a realistic interview question for the {role} role
- Keep it simple, clear, and focused
- DO NOT ask system design questions for Easy/Medium
- DO NOT combine multiple topics

Respond with ONLY the question text.
"""

    model = _get_model()
    response = model.generate_content(prompt)
    return response.text.strip()


# 🚀 FEEDBACK + NEXT QUESTION
def get_feedback_and_next(
    resume,
    experience,
    difficulty,
    topic,
    role,
    history,
    current_question,
    candidate_answer,
):
    topic_line = (
        f"Topic: {topic}"
        if topic
        else f"Topic: vary naturally for a {role} role"
    )

    history_text = ""
    if history:
        pairs = history[-5:]
        history_text = "\n".join(
            f"Q{i+1}: {p['question']}\nA{i+1}: {p['answer']}"
            for i, p in enumerate(pairs)
        )

    prompt = f"""You are a professional technical interviewer.

The candidate is applying for: {role}

Candidate Resume:
{resume[:2000]}

Experience Level: {experience}
Difficulty Level: {difficulty}
{topic_line}

Previous Q&A:
{history_text or "None"}

Current Question:
{current_question}

Candidate Answer:
{candidate_answer}

{QUESTION_RULES}

Evaluation Rules:
- Be honest but supportive
- Keep feedback concise
- Focus on key improvements only

Next Question Rules:
- If answer is weak → ask a simpler follow-up on SAME concept
- If answer is strong → move to a NEW topic
- Keep next question SHORT and SINGLE-CONCEPT
- Avoid system design unless difficulty is HARD

Respond ONLY in valid JSON:
{{
  "correctness": "Short evaluation",
  "missing_points": "Key missing ideas",
  "improvements": "How to improve",
  "sample_answer": "Concise ideal answer",
  "encouragement": "Short motivation",
  "next_question": "Short, clear next question"
}}
"""

    model = _get_model()
    response = model.generate_content(prompt)
    raw = _clean_json(response.text)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "correctness": "Could not evaluate properly.",
            "missing_points": "—",
            "improvements": "Try again.",
            "sample_answer": "—",
            "encouragement": "Keep going, you're doing great!",
            "next_question": current_question,
        }