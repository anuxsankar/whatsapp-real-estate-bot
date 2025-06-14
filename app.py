from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)
user_data = {}

def write_to_sheet(phone, user):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Real Estate Leads").sheet1

    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        phone,
        user.get("budget", ""),
        user.get("location", ""),
        user.get("intent", ""),
        user.get("type", "")
    ])


@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.form.get('Body').strip()
    sender = request.form.get('From')
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg in ["reset", "restart"]:
        user_data.pop(sender, None)
        msg.body("🔄 Session reset! Let’s start over.\n\n💸 What's your budget?\n1. ₹15K–₹25K\n2. ₹25K–₹35K\n3. ₹35K–₹50K")
        user_data[sender] = {"step": 1}
        return str(resp)


    user = user_data.get(sender, {"step": 0})
    step = user["step"]

    if step == 0:
        msg.body("💸 What's your budget?\n1. ₹15K–₹25K\n2. ₹25K–₹35K\n3. ₹35K–₹50K\n\nReply with 1, 2, or 3.")
        user["step"] = 1

    elif step == 1:
        budget_map = {"1": "₹15K–₹25K", "2": "₹25K–₹35K", "3": "₹35K–₹50K"}
        if incoming_msg in budget_map:
            user["budget"] = budget_map[incoming_msg]
            msg.body("📍 Preferred location?\n1. Indiranagar\n2. Koramangala\n3. Whitefield\n\nReply with 1, 2, or 3.")
            user["step"] = 2
        else:
            msg.body("Please reply with a valid option (1, 2, or 3) for budget.")

    elif step == 2:
        location_map = {"1": "Indiranagar", "2": "Koramangala", "3": "Whitefield"}
        if incoming_msg in location_map:
            user["location"] = location_map[incoming_msg]
            msg.body("🏠 Are you looking to:\n1. Rent\n2. Buy\n\nReply with 1 or 2.")
            user["step"] = 3
        else:
            msg.body("Please reply with 1, 2, or 3 for location.")

    elif step == 3:
        intent_map = {"1": "Rent", "2": "Buy"}
        if incoming_msg in intent_map:
            user["intent"] = intent_map[incoming_msg]
            msg.body("🛋 Type of home?\n1. 1BHK\n2. 2BHK\n3. 3BHK+\n\nReply with 1, 2, or 3.")
            user["step"] = 4
        else:
            msg.body("Reply with 1 (Rent) or 2 (Buy).")

    elif step == 4:
        type_map = {"1": "1BHK", "2": "2BHK", "3": "3BHK+"}
        if incoming_msg in type_map:
            user["type"] = type_map[incoming_msg]

            try:
                write_to_sheet(sender, user)
            except Exception as e:
                print(f"⚠️ Failed to write to Google Sheets: {e}")

        summary = (
            f"🎉 Thanks! Here's what you shared:\n"
            f"Budget: {user['budget']}\n"
            f"Location: {user['location']}\n"
            f"Looking to: {user['intent']}\n"
            f"Home type: {user['type']}\n\n"
            "We'll get back to you with options soon! 🏡"
        )
        msg.body(summary)
        print(f"📥 New lead from {sender}: {user}")
        user_data.pop(sender)
    else:
        msg.body("Please reply with 1, 2, or 3 for home type.")


    user_data[sender] = user
    return str(resp)
