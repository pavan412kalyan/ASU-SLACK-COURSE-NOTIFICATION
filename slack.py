import os
import slack
slack_token = os.environ["SLACK_API_TOKEN"]
client = slack.WebClient(token=slack_token)
client.chat_postMessage(channel='#course-asu-bot',text='helloworld test')