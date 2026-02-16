import os
import time
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI

# הגדרות
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
app = Flask(__name__)

# --- הגדרת העוזר (שים כאן את ה-ID שהעתקת מהאתר) ---
# בעתיד, נשלוף את זה ממסד נתונים לפי המספר שאליו שלחו הודעה
ASSISTANT_ID = "asst_ukH050BcM0kutfNCdXJAmrTN" 

# --- זיכרון זמני (In-Memory Database) ---
# המילון הזה מחבר בין מספר טלפון לבין ה-Thread שלו ב-OpenAI
# הערה: כש-Render עושה ריסטארט, הזיכרון הזה נמחק. לפרודקשן אמיתי צריך Database.
user_threads = {}

def get_ai_response(message, phone_number):
    # 1. בדיקה אם למשתמש יש כבר שיחה פתוחה
    thread_id = user_threads.get(phone_number)

    if not thread_id:
        # אם אין, פותחים שיחה חדשה (Thread)
        thread = client.beta.threads.create()
        thread_id = thread.id
        user_threads[phone_number] = thread_id
        print(f"New thread created for {phone_number}: {thread_id}")
    else:
        print(f"Resuming thread for {phone_number}: {thread_id}")

    # 2. הוספת ההודעה החדשה לשיחה
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    # 3. הרצת העוזר (Run)
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    # 4. המתנה לתשובה (Polling)
    # ה-Assistant צריך "לחשוב" ולקרוא קבצים, זה לוקח רגע
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1) # מחכים שנייה
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

    # 5. שליפת התשובה הסופית
    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        # התשובה האחרונה היא הראשונה ברשימה
        response_text = messages.data[0].content[0].text.value
        
        # ניקוי הערות שוליים (לפעמים OpenAI מוסיף סימונים כמו [source])
        # אפשר להוסיף כאן לוגיקה לניקוי טקסט
        return response_text
    else:
        return "סליחה, הייתה תקלה בעיבוד הבקשה."

@app.route("/sms", methods=['POST'])
def sms_reply():
    incoming_msg = request.form.get('Body')
    sender_phone = request.form.get('From') # המספר של הלקוח
    
    print(f"Msg from {sender_phone}: {incoming_msg}")

    # שליחה לפונקציה החכמה שלנו
    ai_response = get_ai_response(incoming_msg, sender_phone)
    
    resp = MessagingResponse()
    resp.message(ai_response)
    return str(resp)

if __name__ == "__main__":
    app.run()
