from slack_course_notifier import start_process
from slack_course_notifier import scrape_single_course
import flask
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import os
from dotenv import load_dotenv
import slack
import yaml

app = flask.Flask(__name__)
#os.environ['SIGNING_SECRET_'],

load_dotenv()

slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET_'], '/slack/events', app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN_'])
BOT_ID = client.api_call("auth.test")['user_id']


# def home():
#     #start_process()
#     return '<h1>STARTED<h1>'

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if BOT_ID!=user_id:
        client.chat_postMessage(channel='#course-asu-bot',text="Hi, check description to track course for notifications \n try : /track 26252  /course-id 26252   ")


@app.route('/course-id', methods=['POST'])
def course_id():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    text = data.get('text')
    course_number=text.strip()
    try:
        course_block = scrape_single_course(course_number=course_number)
        message = f" Request By user-id{user_id} \n"
        current_msg =   f''' 
                            course : {course_block['course']}  \n
                            title : {course_block['title']}  \n
                            status : {course_block["status"]} \n
                            class_N : {course_block["class_N"]} \n 
                            open_seats : {course_block["open_seats"]} \n 
                            click here to add  : {course_block["add_class"]}
                            '''
        client.chat_postMessage(
            channel=channel_id, text=message + current_msg)
    except Exception as e:
        print(e)
        msg="CHECK course number" + course_number
        response = client.chat_postEphemeral(
        channel="#course-asu-bot",
        text=f"{msg}",
        user=user_id
        )    
    return Response(), 200

@app.route('/track', methods=['POST'])
def track_course():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    text = data.get('text')
    course_number=text.strip()
    msg=""
    try:
        course_block = scrape_single_course(course_number=course_number)
        current_msg =   f''' 
                        course : {course_block['course']}  \n
                        title : {course_block['title']}  \n
                        status : {course_block["status"]} \n
                        class_N : {course_block["class_N"]} \n 
                        open_seats : {course_block["open_seats"]} \n 
                        click here to add  : {course_block["add_class"]}
                        '''
        course_number=course_block["class_N"]
        course=course_block['course']
        title=course_block['title']
        result = add_user_track(course_number,user_id)
        if result == 1 :
            slackmsg=f"{course_number},{course},{title} is added to your track list :tada:"
        else :
            slackmsg="could not track: some error"    
        response = client.chat_postEphemeral(
        channel="#course-asu-bot",
        text=slackmsg,
        user=user_id
        )      
    except Exception as e:
        print(e)
        msg="Course does not exist - or check format ->" + course_number
        response = client.chat_postEphemeral(
        channel="#course-asu-bot",
        text=f"{msg}",
        user=user_id
        )

    return Response(), 200



def add_user_track(course_number,user_id):
    try:
        with open("track.yaml") as f:
            track_content = yaml.safe_load(f)

        if track_content == None:
            track_content ={}

        if  course_number in track_content  :
            users = track_content[course_number]
            if user_id not in users :
                users.append(user_id)
                track_content[course_number] = users
        else:
            track_content[course_number] = [user_id]
        with open("track.yaml", "w") as f:
            yaml.dump(track_content, f)
        return 1
    except Exception as e:
        print(e)
        return 0







if __name__ == '__main__':
      app.run()