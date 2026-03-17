"""
AI integration module — Gemini API.

All intelligence lives here:
  - generate_first_question()  → opening question for a session
  - get_feedback_and_next()    → evaluate answer + return next question (JSON)
"""

import json
import google.generativeai as genai
from django.conf import settings


def _get_model():
    """
    Initialise Gemini lazily — avoids crashing on startup if the key
    is not yet set (e.g. during `manage.py migrate`).
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-3-flash-preview")


def _clean_json(raw: str) -> str:
    """Strip markdown code fences Gemini sometimes wraps around JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def generate_first_question(resume, experience, difficulty, topic):
    """
    Generate the opening question for a new interview session.
    Returns a plain string (the question text).
    """
    topic_line = (
        f"Topic: {topic}" if topic
        else "Topic: AI's choice — vary topics naturally across the session"
    )

    prompt = f"""You are a professional technical interviewer starting a real interview.

Candidate Resume:
{resume[:3000]}

Experience Level: {experience}
Difficulty: {difficulty}
{topic_line}

Instructions:
- Ask ONLY ONE interview question
- Make it realistic and role-relevant
- Match the difficulty strictly
- Do NOT include any preamble or explanation — just the question itself

Respond with ONLY the question text. Nothing else."""

    model = _get_model()
    response = model.generate_content(prompt)
    return response.text.strip()


def get_feedback_and_next(resume, experience, difficulty, topic,
                          history, current_question, candidate_answer):
    """
    Evaluate the candidate's answer and generate the next question.

    Returns a dict with keys:
        correctness, missing_points, improvements,
        sample_answer, encouragement, next_question
    """
    topic_line = (
        f"Topic: {topic}" if topic
        else "Topic: not fixed — switch topics naturally based on performance"
    )

    history_text = ""
    if history:
        pairs = history[-5:]
        history_text = "\n".join(
            f"Q{i+1}: {p['question']}\nA{i+1}: {p['answer']}"
            for i, p in enumerate(pairs)
        )

    prompt = f"""You are a professional technical interviewer evaluating a candidate's answer.

Candidate Resume:
{resume[:2000]}

Experience Level: {experience}
Difficulty: {difficulty}
{topic_line}

Previous Q&A History:
{history_text or "None (this is the first question)"}

Current Question:
{current_question}

Candidate's Answer:
{candidate_answer}

Your Tasks:
1. Evaluate the answer honestly but supportively.
2. Generate the NEXT interview question based on performance:
   - If answer was weak → go deeper on the same concept
   - If answer was strong → move to a new relevant topic
   - Always respect the difficulty level
   - If topic is fixed → stay within it
   - If topic is free → vary topics naturally

Respond ONLY with a valid JSON object (no markdown fences, no extra text):
{{
  "correctness": "Was the answer correct? Explain briefly.",
  "missing_points": "Key points the candidate missed.",
  "improvements": "Specific suggestions to improve the answer.",
  "sample_answer": "A concise ideal answer.",
  "encouragement": "One encouraging sentence.",
  "next_question": "The next interview question (just the question text)."
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
