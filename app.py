from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from database import save_user, get_user, save_history, get_history
from dotenv import load_dotenv
from rag import retrieve_context
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "diagnoseme_secret_123"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    name = data.get("name", "").strip()
    user = get_user(name)
    if user:
        session["user_id"] = user[0]
        session["user_profile"] = f"Name: {user[1]}, Age: {user[2]}, Gender: {user[3]}, Allergies: {user[4]}, Conditions: {user[5]}, Medications: {user[6]}"
        past = get_history(user[0])
        past_context = ""
        if past:
            past_context = "\nPast diagnosis history:\n"
            for date, summary in past:
                past_context += f"- [{date}] {summary}\n"
        session["past_context"] = past_context
        session["conversation"] = [{"role": "system", "content": build_system_prompt(session["user_profile"], past_context)}]
        return jsonify({"status": "existing", "name": user[1], "past": [{"date": d, "summary": s} for d, s in past]})
    return jsonify({"status": "new", "name": name})

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get("name").strip()
    age = data.get("age")
    gender = data.get("gender")
    allergies = data.get("allergies")
    conditions = data.get("conditions")
    medications = data.get("medications")
    user_id = save_user(name, age, gender, allergies, conditions, medications)
    session["user_id"] = user_id
    user_profile = f"Name: {name}, Age: {age}, Gender: {gender}, Allergies: {allergies}, Conditions: {conditions}, Medications: {medications}"
    session["user_profile"] = user_profile
    session["past_context"] = ""
    session["conversation"] = [{"role": "system", "content": build_system_prompt(user_profile, "")}]
    return jsonify({"status": "ok", "name": name})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message")
    retrieved_docs = retrieve_context(user_input)

    context = "\n\nRelevant medical knowledge:\n"
    for doc in retrieved_docs:
        context += f"{doc}\n\n"

    conversation = session.get("conversation", [])

    conversation = [conversation[0]] + [
        msg for msg in conversation[1:]
        if "Relevant medical knowledge" not in msg.get("content", "")
    ]

    conversation.append({"role": "user", "content": user_input})
    conversation.insert(1, {
        "role": "system",
        "content": context
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation
    )

    ai_reply = response.choices[0].message.content

    conversation.append({"role": "assistant", "content": ai_reply})
    session["conversation"] = conversation

    return jsonify({"reply": ai_reply})

@app.route("/save", methods=["POST"])
def save():
    conversation = session.get("conversation", [])
    user_id = session.get("user_id")
    summary_convo = conversation.copy()
    summary_convo.append({"role": "user", "content": "Summarize this diagnosis session in one short sentence."})
    summary_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=summary_convo
    )
    summary = summary_response.choices[0].message.content
    save_history(user_id, summary)
    return jsonify({"status": "saved", "summary": summary})

def build_system_prompt(user_profile, past_context):
   return f"""You are DiagnoseMe, a smart and conversational medical AI. Your personality is like a calm, knowledgeable friend who understands basic medicine.

Rules:
- Keep responses SHORT unless more detail is genuinely needed
- Match the user's tone, but stay clear and respectful
- If they go off topic, briefly respond then bring it back
- Never lecture or moralize
- Ask ONE question at a time, keep it natural
- Use the person's name rarely, not every message
- No long paragraphs. Be clear and to the point

Questioning & Diagnosis:
- Ask a few relevant follow-up questions (typically 2–4)
- Do NOT keep asking questions once you have enough information
- When you have enough info, give a short, clear diagnosis
- Focus on the overall symptom pattern, not just one symptom
- Prefer common conditions that match MOST symptoms
- Avoid jumping to rare or unrelated conditions

Response Style:
- Be natural and conversational, not robotic
- Do NOT say "it's too early to tell"
- Give the best possible answer based on current symptoms
- End by suggesting seeing a doctor if needed, in a calm and normal way

When giving a diagnosis, use this format:

Possible Conditions:
- Condition 1
- Condition 2

Risk Level: Low / Moderate / High

Advice:
- Step 1
- Step 2

Patient Profile:
{user_profile}

Previous Context:
{past_context}
"""


if __name__ == "__main__":
    app.run(debug=True)
