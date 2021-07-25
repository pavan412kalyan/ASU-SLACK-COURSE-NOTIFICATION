# -*- coding: utf-8 -*-
#!pip install BeautifulSoup
import requests
from bs4 import BeautifulSoup
from pandas import DataFrame
from threading import Thread
import pandas as pd
import re,time


def scrape(url,all_pages) :
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
        all_pages.append(course_block)
    print(url,"done")
        #seats_span[4]

 
def start_scrape(all_pages) :     
    url="https://webapp4.asu.edu/catalog/myclasslistresults?t=2217&hon=F&promod=F&e=all&s=cse&page=1"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    process_page = Thread(target=scrape, args=[url,all_pages])
    process_page.start()                
    try :
        last_page = soup.find('ul',{'class':'pagination'}).findAll('a',{'class':'change-page'})[-1].text
#        last_page=3
        for i in range(2,int(last_page)+1) :
            url="https://webapp4.asu.edu/catalog/myclasslistresults?t=2217&hon=F&promod=F&e=all&s=cse&page=" + str(i)
            process_page = Thread(target=scrape, args=[url,all_pages])
            process_page.start()
            process_page.join()

    except :
        pass



def start(old_open_seats_dict,old_closed_seats_dict):
    #####    
    all_pages=[]
    start_scrape(all_pages) 
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
    
    print(now_opened,"opened justnow")
    
    
    now_closed=closed_seats_dict-old_closed_seats_dict
    print(now_closed,"closed justnow")
    
    
    old_open_seats_dict=open_seats_dict
    old_closed_seats_dict=closed_seats_dict
    
    
    
    time.sleep(5)
    start(old_open_seats_dict,old_closed_seats_dict)
    
    
#course_number='76277'
#my_course=df[df['class_N']==course_number.strip()]

def check() :
     old_open_seats_dict= set()
     old_closed_seats_dict=set()
     start(old_open_seats_dict,old_closed_seats_dict)


check()
    

   
#find_by_class_url=https://webapp4.asu.edu/catalog/myclasslistresults?t=2217&hon=F&promod=F&e=all&k=76277    
    
    
    
    
    
    

    
    
    
    
    
    
    