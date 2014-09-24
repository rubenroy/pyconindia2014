import requests
import re
from bs4 import BeautifulSoup
#Return RFC 3339 datetime with IST timezone
def getDateTime(day,hour,minute):
	hour_str=str(hour)
	minute_str=str(minute)
	if(hour<10):
		hour_str = "0"+hour_str
	if(minute<10):
		minute_str = "0"+minute_str
	return "2014-09-"+str(day)+"T"+hour_str+":"+minute_str+":00+05:30"

def process_block(events,event_items,start,end):
	for event_item in event_items:
		audi = event_item.find(class_="audi")
		location = ""
		if audi:
			location = audi.get_text().strip()
		details = event_item.find(class_="details")
		title = details.find(class_="title")
		summary = title.get_text().strip()
		if not summary:
			continue
		link = title.a['href']
		description = ""
		if link != "" and "funnel" in link:
			description = get_funnel(link)
		speaker = details.find(class_="speaker").get_text().strip()
		if speaker:
			summary = summary + " by "+speaker
		events.append({
			'summary': str(summary),
			'location': str(location),
			'description':str(description),
			'start': {
				'dateTime': str(start)
			},
			'end': {
				'dateTime': str(end)
			}
		})
def get_events():
	events = [];
	day = 26
	soup =  BeautifulSoup(requests.get("http://in.pycon.org/2014/schedule.html").text)
	schedules = soup.find_all(class_="schedule-wrapper")
	workshops = schedules[0]
	block_times = workshops.find_all(class_="block-time")
	for block in block_times:
		time = block.h3.get_text().lower()
		hour = int(time[:2])
		minute = int(time[3:5])
		if time[5]=='p':
			hour = hour + 12
		start = getDateTime(day,hour,minute)
		end = ""
		common_event = block.find(class_="common-event")
		if common_event:
			if minute<30:
				end = getDateTime(day,hour,minute+30)
			else:
				end = getDateTime(day,hour+1,minute-30)		
			events.append({
				'summary': str(common_event.get_text().strip()),
				'description':str(""),		
				'start': {
					'dateTime': str(start)
				},
				'end': {
					'dateTime': str(end)
				}
			})
		events_list = block.find(class_="events-list")
		if events_list:
			end = getDateTime(day,hour+3,minute)
			event_items = events_list.find_all(class_="event-item")
			process_block(events,event_items,start,end)
	day = 27
	for schedule in schedules[1:3]:
		block_times = schedule.find_all(class_="block-time")
		for block in block_times:
			times = block.h3.get_text().replace(' - ','.').split('.')
			start = getDateTime(day,int(times[0]),int(times[1]))
			end = getDateTime(day,int(times[2]),int(times[3]))
			event_items = block.find_all(class_="event-item")
			process_block(events,event_items,start,end)
		day = 28
	return events

def get_funnel(url):
	if url == "":
		return ""
	html = requests.get(url).text
	html = ''.join([i if ord(i) < 128 else '' for i in html])
	soup =  BeautifulSoup(html)
	response = "Speaker:"+soup.strong.get_text()+"\n"
	infosheet = soup.find(class_="infosheet")
	bar_items = infosheet.find(class_="bar").findChildren()
	response = response + bar_items[1].get_text()+":"+bar_items[2].get_text()+"\n" \
				+ bar_items[3].get_text()+":"+bar_items[4].get_text()+"\n"
	sections = infosheet.find_all(class_="section")
	for section in sections[2:]:
		children = section.findChildren()
		for tag in children:
			if tag.name == "h2":
				if tag.get_text() == "Comments":
					break
				response = response +"\n" + tag.get_text().upper()+"\n"
			elif tag.name == "p":
				response = response + "\n" + str(tag.text).replace("<br/>","") + "\n"
				re.compile("r'<.*?>'").sub("",response)
			elif tag.name == "ul":
				response = response + tag.get_text()			
	response = response + "Funnel Page: "+url+"\n"
	return response
