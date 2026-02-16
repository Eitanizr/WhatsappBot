import os
import time
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI

# הגדרות מפתח
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
app = Flask(__name__)

# --- שים לב: כאן מדביקים את המזהה בתוך הגרשיים ---
ASSISTANT_ID = "asst_ukH050BcM0kutfNCdXJAmrTN" 
# דוגמה: ASSISTANT_ID = "asst_ABC123..."
# ------------------------------------------------

# זיכרון זמני
user_threads = {}

def get_ai_response(message, phone_number):
    try:
        thread_id = user_threads.get(phone_number)
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            user_threads[phone_number] = thread_id
            print(f"New thread: {thread_id}")
        
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        # המתנה לתשובה
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            return messages.data[0].content[0].text.value
        else:
            print(f"Run status: {run.status}")
            return "סליחה, יש עיכוב בתשובה."
            
    except Exception as e:
        print(f"Error in get_ai_response: {e}")
        return "יש תקלה טכנית בבוט כרגע."

# בדיקת דופק ל-Render
@app.route("/", methods=['GET'])
def home():
    return "Alive and kicking!", 200

# קבלת הודעה מווטסאפ
@app.route("/sms", methods=['POST'])
def sms_reply():
    incoming_msg = request.form.get('Body')
    sender_phone = request.form.get('From')
    print(f"Message from {sender_phone}: {incoming_msg}")
    
    ai_response = get_ai_response(incoming_msg, sender_phone)
    
    resp = MessagingResponse()
    resp.message(ai_response)
    return str(resp)

if __name__ == "__main__":
    # פורט קבוע למניעת בלבול
    app.run(host='0.0.0.0', port=10000)
