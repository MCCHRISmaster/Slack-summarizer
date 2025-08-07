import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI


from dotenv import load_dotenv

load_dotenv()

# Load keys from .env file
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_NAME = "social"  # change to your channel name

client = WebClient(token=SLACK_TOKEN)

def get_channel_id(channel_name):
    response = client.conversations_list()
    print(response)
    for channel in response['channels']:
        if channel["name"] == channel_name:
            return channel["id"]
    return None

def fetch_messages(channel_id):
    response = client.conversations_history(channel=channel_id, limit=50)
    messages = [msg["text"] for msg in response['messages'] if "text" in msg]
    return "\n".join(reversed(messages))

def summarize(text):
    response = client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": "Summarize this Slack incident chat:"},
        {"role": "user", "content": text}
    ])
    return response.choices[0].message.content

def is_bot_in_channel(channel_name):
    response = client.conversations_list()
    for channel in response["channels"]:
        if channel["name"] == channel_name:
            return channel["is_member"]
    return False

print(f"Is bot in '{CHANNEL_NAME}'? → {is_bot_in_channel(CHANNEL_NAME)}")

def main():
    response = client.conversations_list()
    print(response)
    channel_id = get_channel_id(CHANNEL_NAME)
    if not channel_id:
        print("Channel not found.")
        return

    messages = fetch_messages(channel_id)
    print("\n🔹 Messages Fetched:\n", messages[:500], "...\n")

    summary = summarize(messages)
    print("\n✅ Summary:\n", summary)

if __name__ == "__main__":
    main()