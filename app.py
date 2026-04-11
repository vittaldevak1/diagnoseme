from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from database import save_user, get_user, save_history, get_history
from dotenv import load_dotenv
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
    conversation = session.get("conversation", [])
    conversation.append({"role": "user", "content": user_input})
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
    return f"""You are DiagnoseMe, a smart and witty medical AI. Your personality is like a clever 
friend who happens to know medicine. Rules:
- Keep responses SHORT unless more detail is genuinely needed
- Match the user's energy. If they're being casual and funny, be casual and funny back
- If they go off topic, play along BRIEFLY then bring it back in one line
- Never lecture or moralize
- Never use "as a medical AI" or "as a friendly assistant"
- Ask ONE question at a time, keep it casual
- Use the person's name rarely, not every message
- No long paragraphs. Get to the point.
- Never suggest a diagnosis until you've asked at least 5-6 follow up questions
- When you have enough info, give a short clear diagnosis
- Always end with recommending a real doctor, but say it casually like a friend would
- You DO have memory of past sessions, use the history below to reference past visits

Patient profile:
{user_profile}
{past_context}"""

if __name__ == "__main__":
    app.run(debug=True)
