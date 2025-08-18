from flask import Flask, render_template, request, send_from_directory
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from datetime import datetime
import os
from incident_summary import summarize, save_summary_as_pdf, fetch_messages, get_channel_id, last_incident, get_filtered_messages

load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "summaries"

slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def list_my_channels():
    try:
        response = slack_client.conversations_list()
        return [ch["name"] for ch in response["channels"] if ch.get("is_member")]
    except SlackApiError as e:
        print(f"Slack API error: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    summary = ""
    pdf_filename = ""
    channels = list_my_channels()
    form_type = request.form.get("form_type")

    if request.method == "POST":
        selected_channel = request.form.get("channel")
        if not selected_channel:
            summary = "⚠️ No channel selected!"
        else:
            channel_id = get_channel_id(selected_channel)
            if not channel_id:
                summary = "⚠️ Channel not found!"
            else:
                if form_type == "last_incident_filter":
                    messages = fetch_messages(channel_id)
                    incident_msgs = last_incident(messages)
                    summary = summarize(incident_msgs)
                    pdf_filename = save_summary_as_pdf(summary, folder=app.config["UPLOAD_FOLDER"])
                elif form_type == "date_filter":
                    start_date = request.form.get("start_date")
                    end_date = request.form.get("end_date")
                    keywords = request.form.get("keywords")
                    users = request.form.get("users")

                    # Convert the dates
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

                    keyword_list = [k.strip() for k in keywords.split(",")] if keywords else None
                    user_list = [u.strip() for u in users.split(",")] if users else None

                    filtered_msgs = get_filtered_messages(
                        channel_id, 
                        start_date=start_dt, 
                        end_date=end_dt,
                        keywords=keyword_list,
                        users=user_list
                    )
                    summary = summarize(filtered_msgs)
                    pdf_filename = save_summary_as_pdf(summary, folder=app.config["UPLOAD_FOLDER"])

    return render_template("index.html", summary=summary, pdf=pdf_filename, channels=channels)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)