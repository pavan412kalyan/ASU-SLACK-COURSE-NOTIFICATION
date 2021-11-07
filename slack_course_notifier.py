import os
import slack
from pathlib import Path
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from pandas import DataFrame
from threading import Thread
import pandas as pd
import re,time
import yaml


load_dotenv()
slack_token = os.environ["SLACK_API_TOKEN"]
#export SLACK_API_TOKEN="xoxb-2252735053767-2291169237728-0U0nuv3BFRw58MXlDbH8rGqi"
# client = slack.WebClient(token='xoxb-2252735053767-2291169237728-0U0nuv3BFRw58MXlDbH8rGqi')
client = slack.WebClient(token=slack_token)
client.chat_postMessage(channel='#course-asu-bot',text='ASU COURSE NOTIFIER slack bot restarted')
#!pip install BeautifulSoup


def scrape_single_course(course_number,term=2221):
    #url='https://webapp4.asu.edu/catalog/myclasslistresults?t=2221&hon=F&promod=F&e=all&k=76277'
    url=f'https://webapp4.asu.edu/catalog/myclasslistresults?t={term}&hon=F&promod=F&e=all&k={course_number}'
    print(url)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    body = soup.find("tbody")
    r = body.find('tr')
    #there will be only one row
    course_block={}  
    course = r.find('td',{'class':'subjectNumberColumnValue'}).text.strip()
    course_block['course']=course
    title = r.find('td',{'class':'titleColumnValue'}).text.strip()
    title   = re.sub(r"[\n\t]*", "", title)

    course_block['title']=title

    class_N = r.find('td',{'class':'classNbrColumnValue'}).text.strip()
    course_block['class_N']=class_N

    days = r.find('td',{'class':'dayListColumnValue'}).text.strip()
    course_block['days']=days

    startTime = r.find('td',{'class':'startTimeDateColumnValue'}).text.strip()
    course_block['startTime']=startTime

    endTime = r.find('td',{'class':'endTimeDateColumnValue'}).text.strip()
    course_block['endTime']=endTime

    location = r.find('td',{'class':'locationBuildingColumnValue'}).text.strip()
    course_block['location']=location

    dates = r.find('td',{'class':'startDateColumnValue'}).text.strip()
    course_block['dates']=dates

    units = r.find('td',{'class':'hoursColumnValue'}).text.strip()
    course_block['units']=units

    seats_span = r.find('td',{'class':'availableSeatsColumnValue'}).findAll('span')
#        course_block['seats_span']=seats_span

    open_seats=seats_span[0].text.strip()#available
    course_block['open_seats']=open_seats

        #seats_span[1]#of
    total_seats=seats_span[2].text.strip()#total seats
    course_block['total_seats']=total_seats

    status=seats_span[3].find('i')['title']
    course_block['status']=status

    #add class link
    course_block['add_class']=f'https://www.asu.edu/go/addclass/?STRM={term}&ASU_CLASS_NBR={course_number}'

    
    return course_block



def scrape(url,all_pages,term,course) :
    print(url)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    body = soup.find("tbody")
    rows = body.findAll('tr')
    for r in rows : 
        course_block={}  
        course = r.find('td',{'class':'subjectNumberColumnValue'}).text.strip()
        course_block['course']=course
        title = r.find('td',{'class':'titleColumnValue'}).text.strip()
        title   = re.sub(r"[\n\t]*", "", title)

        course_block['title']=title

        class_N = r.find('td',{'class':'classNbrColumnValue'}).text.strip()
        course_block['class_N']=class_N

        days = r.find('td',{'class':'dayListColumnValue'}).text.strip()
        course_block['days']=days

        startTime = r.find('td',{'class':'startTimeDateColumnValue'}).text.strip()
        course_block['startTime']=startTime

        endTime = r.find('td',{'class':'endTimeDateColumnValue'}).text.strip()
        course_block['endTime']=endTime

        location = r.find('td',{'class':'locationBuildingColumnValue'}).text.strip()
        course_block['location']=location

        dates = r.find('td',{'class':'startDateColumnValue'}).text.strip()
        course_block['dates']=dates

        units = r.find('td',{'class':'hoursColumnValue'}).text.strip()
        course_block['units']=units

        seats_span = r.find('td',{'class':'availableSeatsColumnValue'}).findAll('span')
#        course_block['seats_span']=seats_span

        open_seats=seats_span[0].text.strip()#available
        course_block['open_seats']=open_seats

        #seats_span[1]#of
        total_seats=seats_span[2].text.strip()#total seats
        course_block['total_seats']=total_seats

        status=seats_span[3].find('i')['title']
        course_block['status']=status
         
        try: 
            course_block['add_class']=f'https://www.asu.edu/go/addclass/?STRM={term}&ASU_CLASS_NBR={class_N}'
        except:
            course_block=""
            

        all_pages.append(course_block)
    print(url,"done")
        #seats_span[4]
 
def start_scrape(all_pages,url,term,course) :     
    url=url
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    process_page = Thread(target=scrape, args=[url,all_pages,term,course])
    process_page.start()                
    try :
        last_page = soup.find('ul',{'class':'pagination'}).findAll('a',{'class':'change-page'})[-1].text
#        last_page=3
        for i in range(2,int(last_page)+1) :
            #PAGE URLS HERE
            page_url= url + "&page="+ str(i)
            process_page = Thread(target=scrape, args=[page_url,all_pages,term,course])
            process_page.start()
            process_page.join()
    except Exception as e:          
        print(e)



def  start(old_open_seats_dict,old_closed_seats_dict,url,term,course):
    #####    
    all_pages=[]
    start_scrape(all_pages,url,term,course)
    df = pd.DataFrame(all_pages)
    
    #############
    open_seats=df[df['status']=='seats available']
    open_seats_course_N = list(open_seats['class_N'])
    open_seats_dict= set()
    for s in open_seats_course_N :
        open_seats_dict.add(s)
    
    ###
    closed_seats=df[df['status']=='seats unavailable']
    closed_seats_course_N = list(closed_seats['class_N'])
    closed_seats_dict= set()
    for s in closed_seats_course_N :
        closed_seats_dict.add(s)
    
    ############
    reserved_seats=df[df['status']=='seats reserved']
    reserved_seats_course_N = list(reserved_seats['class_N'])
    reserved_seats_dict= set()
    for s in reserved_seats_course_N :
        reserved_seats_dict.add(s)
    
    now_opened=open_seats_dict-old_open_seats_dict

    ##OPENED
    print(len(now_opened))
    if len(now_opened) > 0 :
      msg=""
      for course_num in list(now_opened) :
        X=df[df['class_N']==course_num]
        course = X.iloc[0]['course']
        title = X.iloc[0]['title']
        status = X.iloc[0]['status']
        class_N = X.iloc[0]['class_N']
        open_seats = X.iloc[0]['open_seats']
        add_class = X.iloc[0]['add_class']
        current_msg =   f''' 
                        course : {course}  \n
                        title : {title}  \n
                        status : {status} \n
                        class_N : {class_N} \n 
                        open_seats : {open_seats} \n 
                        '''

        msg = msg + "  \n" + current_msg

        notify_users(course_num,course,open_seats,title,add_class)
      #NOTIFY CHANNEL notfies all mem
      #to avoid 1st iterations
      if len(now_opened) <=15 :
        client.chat_postMessage(channel='#course-asu-bot',text='Courses'+ msg + "  is now opened")

    now_closed=closed_seats_dict-old_closed_seats_dict
    #print(now_closed,"closed justnow")

    if len(now_closed) > 0 :
      msg = ""
      for course_num in list(now_closed) :
        X=df[df['class_N']==course_num]
        course = X.iloc[0]['course']
        title = X.iloc[0]['title']
        status = X.iloc[0]['status']
        class_N = X.iloc[0]['class_N']
        open_seats = X.iloc[0]['open_seats']
        add_class = X.iloc[0]['add_class']



        current_msg =   f''' 
                        course : {course}  \n
                        title : {title}  \n
                        status : {status} \n
                        class_N : {class_N} \n 
                        open_seats : {open_seats} \n 
                        '''
        msg = msg + "  \n" + current_msg
      #client.chat_postMessage(channel='#course-asu-bot',text='Courses'+ msg + "  is now closed")


    
    old_open_seats_dict=open_seats_dict
    old_closed_seats_dict=closed_seats_dict
    
 
    time.sleep(5)
    start(old_open_seats_dict,old_closed_seats_dict,url,term,course)
    
    
#course_number='76277'
#my_course=df[df['class_N']==course_number.strip()]

def check(term,course,url) :
     old_open_seats_dict= set()
     old_closed_seats_dict=set()
     try :
         start(old_open_seats_dict,old_closed_seats_dict,url,term,course)
     except Exception as e:          
        print(e)
        check(term,course,url)
     

def start_process():
    term='2221'
    course='cse'
    check(term,course,url=f'https://webapp4.asu.edu/catalog/myclasslistresults?t={term}&hon=F&promod=F&e=all&s={course}')
 
    
#find_by_class_url=https://webapp4.asu.edu/catalog/myclasslistresults?t=2221&hon=F&promod=F&e=all&k=76277    
# x=scrape_single_course(course_number=76277,term=2221)
# print(x)


#NOTIFIES ONLY SUBSCRIBED USERS
def notify_users(course_number,course,open_seats,title,add_class):
    with open("track.yaml") as f:
        track_content = yaml.safe_load(f)
    print(track_content,course_number)
    if track_content == None:
        print("track_content",track_content)
        return
    if course_number in track_content:
        users = track_content[course_number]
        for user in users:
            print("NOTIFIED",user)
            response = client.chat_postEphemeral(
            channel="#course-asu-bot",
            text=f"{course_number},{course},{title} {open_seats} are available click {add_class} :tada:",
            user=user
            )

if __name__ == "__main__":
    start_process()
