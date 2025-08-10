from flask import Flask, render_template, request, send_from_directory
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os
from incident_summary import summarize, save_summary_as_pdf, fetch_messages, get_channel_id, check_for_resolution

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

    if request.method == "POST":
        selected_channel = request.form["channel"]
        channel_id = get_channel_id(selected_channel)

        if not channel_id:
            summary = "⚠️ Channel not found!"
        else:
            messages = fetch_messages(channel_id)
            messages = check_for_resolution(messages)
            summary = summarize(messages)
            pdf_filename = save_summary_as_pdf(summary, folder=app.config["UPLOAD_FOLDER"])
           
    return render_template("index.html", summary=summary, pdf=pdf_filename, channels=channels)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)