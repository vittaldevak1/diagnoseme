from groq import Groq
from database import save_user, get_user, save_history, get_history

client = Groq(api_key="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")

print("Welcome to DiagnoseMe AI 🏥")
print("="*40)

def get_valid_input(prompt, input_type="text", options=None):
    while True:
        value = input(prompt).strip()
        if not value:
            print("This field cannot be empty, please try again.")
            continue
        if input_type == "number":
            if value.isdigit() and 1 <= int(value) <= 120:
                return value
            print("Please enter a valid number between 1 and 120.")
        elif input_type == "options" and options:
            if value.lower() in options:
                return value.lower()
            print(f"Please enter one of: {', '.join(options)}")
        elif input_type == "text":
            if value.replace(" ", "").isalpha() or value.lower() == "none":
                return value
            print("Please enter text only, no numbers or special characters.")
        elif input_type == "freetext":
            return value

name = get_valid_input("Enter your name: ", "text")

existing_user = get_user(name)

if existing_user:
    print(f"\nWelcome back, {existing_user[1]}! 👋")
    user_id = existing_user[0]
    user_profile = f"""
    Name: {existing_user[1]}, Age: {existing_user[2]}, Gender: {existing_user[3]}
    Allergies: {existing_user[4]}, Conditions: {existing_user[5]}, Medications: {existing_user[6]}
    """
    past = get_history(user_id)
    if past:
        print("\nYour past diagnoses:")
        for date, summary in past:
            print(f"  [{date}] {summary}")
        print()
    past_context = ""
    if past:
        past_context = "\nPast diagnosis history:\n"
        for date, summary in past:
            past_context += f"- [{date}] {summary}\n"
else:
    print("\nFirst time here! Let's get your details.\n")
    age = get_valid_input("Age: ", "number")
    gender = get_valid_input("Gender (male/female/other): ", "options", ["male", "female", "other"])
    allergies = get_valid_input("Any known allergies? (or type 'none'): ", "freetext")
    conditions = get_valid_input("Any existing medical conditions? (or type 'none'): ", "freetext")
    medications = get_valid_input("Any current medications? (or type 'none'): ", "freetext")
    user_id = save_user(name, age, gender, allergies, conditions, medications)
    user_profile = f"""   Name: {name}, Age: {age}, Gender: {gender}
    Allergies: {allergies}, Conditions: {conditions}, Medications: {medications}
    """
    past_context = ""
    print(f"\nProfile saved! Welcome, {name} 🎉\n")

conversation = [
    {"role": "system", "content": f"""You are DiagnoseMe, a smart and witty medical AI. Your personality is like a clever 
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
{past_context}"""}
]

print("Type 'quit' to exit\n")
print("AI: What's going on today?")

while True:
    user_input = input("You: ")

    if user_input.lower() == "quit":
        print("\nAI: Before you go — want me to save a summary of today's session? (yes/no)")
        save = input("You: ").strip().lower()
        if save == "yes":
            summary_convo = conversation.copy()
            summary_convo.append({"role": "user", "content": "Summarize this diagnosis session in one short sentence."})
            summary_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=summary_convo
            )
            summary = summary_response.choices[0].message.content
            save_history(user_id, summary)
            print(f"AI: Saved! Take care, see a real doctor if needed 👊")
        else:
            print("AI: Alright, take care!")
        break

    conversation.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation
    )

    ai_reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": ai_reply})

    print(f"\nAI: {ai_reply}\n")
