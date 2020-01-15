from flask import Flask
from flask import request,render_template, jsonify
import json
import datetime
import calendar
import time
import helpers
import requests
import os
import csv
import folium
print (os.getcwd())

app=Flask(__name__,static_url_path="/static")

apipath="/"
dblocation="helpers/testincident.db"
locationfile='helpers/locs.csv'
#/home/pi/Documents/tfwmalerts/bccalerts/api/alertapi/database

@app.route("/")
def worst():
	n=requests.get("http://localhost/events").json()
	print n
	passer=[]
	for row in n['response']['results']:
		if row:
			tmp=[]
			tmp.append(row['uuid'])
			tmp.append(row['sensor'])
			tmp.append(datetime.datetime.fromtimestamp(int(row['starttime'])).strftime('%H:%M:%S'))
			tmp.append(str(int(time.time()-float(row['starttime']))/60)+' minutes')
			tmp.append(row['info'])
			tmp.append(row['severity'])
			passer.append(tmp)
		print (passer)
	return render_template('worst.html', posts=passer)

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
	elif "current" in args or len(args)==0:
		ret['extents']={'end':-1}
	if 'extents' in ret:
		if ret['extents']['end']==-1:
			n=helpers.incidentdatabase(fileloc=dblocation).querylive()
			print ([l for l in n])
			ret['results']=[dict(l) for l in n]
		else:
			n=helpers.incidentdatabase(fileloc=dblocation).querydate(start=ret['extents']['start'],end=ret['extents']['end'])
			ret['results']=[dict(l) for l in n]
	
	return jsonify({'response':ret})

@app.route(apipath+"locations")
def locs():
	ret={}
	args=request.args.to_dict()
	with open(locationfile,'r') as csvfile:
		reader=csv.DictReader(csvfile)
		tmp=[]
		for row in reader:
			try:
				dat={}
				dat['id']=row['ID']
				dat['type']=row['Sensor Type']
				dat['generation']=row['Generation']
				dat['location']={'description':row['Description'],'class':row['Road Class'],'direction':row['Compass Direction'],'points':[(float(n.split(':')[0]), float(n.split(':')[1])) for n in row['Points'].split('|')]}
				tmp.append(dat)
			except:
				continue
	ret['query']='All Data'
	ret['data']=tmp
	if 'id' in args:
		if args['id'] in [n['id'] for n in ret['data']]:
			ret['data']=[n for n in ret['data'] if n['id']==args['id']]
			ret['query']={'id':args['id']}
	if 'type' in args:
		if args['type'] in [n['type'] for n in ret['data']]:
			ret['data']=[n for n in ret['data'] if n['type']==args['type']]
			ret['query']={'type':args['type']}
	return jsonify(ret)

def apierror(text):
	return {'error':text}
	
def stampfromdate(dt):
	dt=datetime.datetime(dt.year,dt.month,dt.day)
	return calendar.timegm(dt.timetuple())
	
@app.route(apipath+"locationmap")
def locmap():
	j=requests.get("http://localhost/locations").json()
	d,e=0,0

	for a in j['data']:
		print a['location']['points']
		d+=sum([n[0] for n in a['location']['points']])/len(a['location']['points'])
		e+=sum([n[1] for n in a['location']['points']])/len(a['location']['points'])
	d=d/len(j['data'])
	e=e/len(j['data'])
	print d,e
	m=folium.Map(location=[d,e])
	for a in j['data']:
		if len(a['location']['points'])==1:
			folium.Marker(a['location']['points'][0]).add_to(m)
		else:
			folium.PolyLine(a['location']['points']).add_to(m)
	return m.get_root().render()
