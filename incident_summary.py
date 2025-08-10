import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from anthropic import Anthropic
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime


from dotenv import load_dotenv

load_dotenv()

# Load keys from .env file
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
CHANNEL_NAME = "social"  # change to your channel name

client = WebClient(token=SLACK_TOKEN)
def get_channel_id(channel_name):
    response = client.conversations_list()
    for channel in response['channels']:
        if channel["name"] == channel_name:
            return channel["id"]
    return None

def fetch_messages(channel_id):
    response = client.conversations_history(channel=channel_id, limit=50)
    messages = [msg["text"] for msg in response['messages'] if "text" in msg]
    return "\n".join(reversed(messages))

def summarize(text):
    anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
    response = anthropic_client.messages.create(model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        system="Summarize this Slack incident chat:",
        messages=[
            {"role": "user", "content": text}
        ])
    return response.content[0].text

def is_bot_in_channel(channel_name):
    response = client.conversations_list()
    for channel in response["channels"]:
        if channel["name"] == channel_name:
            return channel["is_member"]
    return False

print(f"Is bot in '{CHANNEL_NAME}'? → {is_bot_in_channel(CHANNEL_NAME)}")

def make_folders_date():
    today = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join("summaries", today)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_summary_as_pdf(summary, filename=None, folder="summaries"):
    if not filename:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"incident_summary_{timestamp}.pdf"

    # Ensure folder exists
    os.makedirs(folder, exist_ok=True)
    # if the date folder is not in summaries, create it
    if not os.path.exists(os.path.join(folder, datetime.now().strftime("%Y-%m-%d"))):
        folder = make_folders_date()
    else:
        folder = os.path.join(folder, datetime.now().strftime("%Y-%m-%d"))    
    


    filepath = os.path.join(folder, filename)
    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("📝 Incident Summary", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(summary, styles["Bullet"]))

    doc.build(elements)
    print(f"✅ Summary saved to {filename}")
    return filename

def check_for_resolution(messages):
    keywords = ["incident resolved", "resolved", "closing incident"]
    message_lines = [msg for msg in messages.split("\n") if msg.strip()]
    if not message_lines:
        return ""

    # Find indices of all resolved messages
    resolved_indices = [
        i for i, msg in enumerate(message_lines)
        if any(keyword in msg.lower() for keyword in keywords)
    ]

    if not resolved_indices:
        return "Incident not resolved yet."

    if len(resolved_indices) == 1:
        # Only one resolved message, return everything before it
        return "\n".join(message_lines[:resolved_indices[0]])

    # Two or more resolved messages, return block between last two (excluding them)
    start = resolved_indices[-2] + 1
    end = resolved_indices[-1]
    return "\n".join(message_lines[start:end])

def main():
    response = client.conversations_list()

    channel_id = get_channel_id(CHANNEL_NAME)
    if not channel_id:
        print("Channel not found.")
        return

    messages = fetch_messages(channel_id)
    print("\n🔹 Messages Fetched:\n", messages[:500], "...\n")

    # save to a pdf
    if check_for_resolution(messages):
        summary = summarize(messages)
        save_summary_as_pdf(summary)
    else:
        print("Incident not resolved yet. Skipping summary.")

if __name__ == "__main__":
    main()