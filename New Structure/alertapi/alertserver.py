from flask import Flask
from flask import request
import json
import datetime
import calendar
import time


app=Flask(__name__,static_url_path="/static")

apipath="/"

@app.route("/")
def helloworld():
	return ('hello')

@app.route(apipath+"events")
def events():
	args=request.args.to_dict()
	ret={}
	ret['input data']=args
		
	#   events starting between (time.time and time.time)
	#   week = this weeks events
	#   day= 'today' or 'datetime.date' todays events
	#	current=(now or time or datetime) current at xxx time (current=now)
	#   no args - get current events
	if "start" in args:
		try:
			start=float(args['start'])
		except ValueError:
			return apierror('start needs to be a integer or float expressing seconds elapsed since 01/01/1970')
		if "end" in args:
			try:
				end=float(args['end'])
			except ValueError:
				return apierror('end needs to be a integer or float expressing seconds elapsed since 01/01/1970')
		else:
			end=time.time()
		ret['extents']={'start':start,'end':end}
	elif "day" in args:
		if args['day']=="today":
			start=datetime.date.today()
			start=stampfromdate(start)
			end=time.time()
		else:
			try:
				start=datetime.datetime.strptime(args['day'],'%d/%m/%Y')
			except ValueError:
				return apierror('date needs to be in the format 01/01/1970')
			start=stampfromdate(start)
			end=start+86400
		ret['extents']={'start':start,'end':end}
	elif "week" in args:
		if args['week']=='this':
			start=datetime.date.today()-datetime.timedelta(days=datetime.date.today().weekday())
			start=stampfromdate(start)
			end=time.time()
		ret['extents']={'start':start,'end':end}
	#### now needs us to add the current bit....
	return json.dumps(ret)

@app.route(apipath+"locations")
def locs():
	return "none"

def apierror(text):
	return {'error':text}
	
def stampfromdate(dt):
	dt=datetime.datetime(dt.year,dt.month,dt.day)
	return calendar.timegm(dt.timetuple())
	
	
