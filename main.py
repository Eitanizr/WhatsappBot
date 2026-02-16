import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI

# כאן אנחנו אומרים לקוד: אל תחפש את המפתח בקוד, חפש אותו בהגדרות השרת
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)

@app.route("/sms", methods=['POST'])
def sms_reply():
    # קבלת ההודעה
    incoming_msg = request.form.get('Body')
    print(f"Message received: {incoming_msg}")

    # הגדרת המוח של הבוט
    system_prompt = "אתה נציג שירות של פיצרייה. ענה בעברית, בקצרה ובנימוס."

    try:
        # שליחה ל-GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": incoming_msg}
            ]
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = "סליחה, יש לי תקלה רגעית. נסה שוב עוד דקה."
        print(f"Error: {e}")

    # שליחה חזרה לווטסאפ
    resp = MessagingResponse()
    resp.message(answer)
    return str(resp)

if __name__ == "__main__":
    app.run()
