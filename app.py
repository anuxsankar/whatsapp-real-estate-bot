from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
user_data = {}

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.form.get('Body').strip().lower()
    sender = request.form.get('From')
    resp = MessagingResponse()
    msg = resp.message()

    user = user_data.get(sender, {"step": 0})

    if user["step"] == 0:
        msg.body("🏡 Hey! I'm your property matchmaker. What's your budget?")
        user["step"] = 1
    elif user["step"] == 1:
        user["budget"] = incoming_msg
        msg.body("📍 Got it! Which locations are you interested in?")
        user["step"] = 2
    elif user["step"] == 2:
        user["location"] = incoming_msg
        msg.body("🛋 Are you looking to *rent* or *buy*?")
        user["step"] = 3
    elif user["step"] == 3:
        user["intent"] = incoming_msg
        msg.body("🏠 What type of home? (e.g. 2BHK, 1RK...)")
        user["step"] = 4
    elif user["step"] == 4:
        user["type"] = incoming_msg
        msg.body("🎯 Noted! We’ll send some listings your way soon. Want to schedule a visit? (yes/no)")
        print(f"New lead: {user}")
        user_data.pop(sender)
    else:
        msg.body("Thank you! Our broker will get back to you 😊")

    user_data[sender] = user
    return str(resp)
