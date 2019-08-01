import andyconfig
import os
import requests
import json
import datetime
import matplotlib.pyplot as plt
print os.environ['ALKEY']
import numpy as np

period=56

class parking():
	def __init__(self):
		
		n=requests.get("http://bcc.opendata.onl/UTMC Parking.json?ApiKey="+os.environ['ALKEY'])
		self.data=n.json()
		#print json.dumps(self.data,indent=2)
		
	
	def allsites(self):
		return [n['SCN']['content'] for n in self.data['Parking']['Carpark']]
		
	def allloops(self):
		ret=[]
		for n in self.data['Parking']['Carpark']:
			try:
				ret.append([n['SCN']['content'], int((datetime.datetime.now()-datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)])
			except TypeError:
				continue
		return ret
		
	def findcurrentdata(self,site,removezeroes=False):
		ret=[]
		for n in self.data['Parking']['Carpark']:
			if n['SCN']['content']==site:
				#if removezeroes:
				#	if n['Speed']+n['Cars']+n['Trailers']+n['Rigids']+n['Buses']+n['Motorbikes']==0:
				#		continue
				ret.append([n['Occupancy']['Percent'], int((datetime.datetime.now()-datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)])
		return ret

						
	def findhistoricdata(self,site,start=str((datetime.datetime.now()-datetime.timedelta(days=period)).date()),end=str(datetime.datetime.now().date()),removezeroes=False):
		url="http://bcc.opendata.onl/UTMC Parking.json?"+"SCN="+str(site)+"&TS=true&Earliest="+start+"&Latest="+end+"&ApiKey="+os.environ['ALKEY']		
		n=requests.get(url)
		res=n.json()
		ret={}
		old=res['Parking']['Data']['Occupancy'][0]['content']
		olddate=datetime.datetime.strptime(res['Parking']['Data']['Date'][0],"%Y-%m-%d %H:%M:%S")
		for x in range(len(res['Parking']['Data']['Occupancy'])-1):
			if datetime.datetime.strptime(res['Parking']['Data']['Date'][x+1],"%Y-%m-%d %H:%M:%S")==olddate:
				continue
			ret[datetime.datetime.strptime(res['Parking']['Data']['Date'][x],"%Y-%m-%d %H:%M:%S")]=(res['Parking']['Data']['Occupancy'][x+1]['content']-old)/float((datetime.datetime.strptime(res['Parking']['Data']['Date'][x+1],"%Y-%m-%d %H:%M:%S")-olddate).total_seconds()/3600)
			old=res['Parking']['Data']['Occupancy'][x]['content']
			olddate=datetime.datetime.strptime(res['Parking']['Data']['Date'][x+1],"%Y-%m-%d %H:%M:%S")
		#for x in range(len(res['Parking']['Data']['Occupancy'])):
		#		ret[datetime.datetime.strptime(res['Parking']['Data']['Date'][x],"%Y-%m-%d %H:%M:%S")]=res['Parking']['Data']['Occupancy'][x]['Percent']
				
		
		return ret
		

'''What does this do?
The aim is to identify abnormally low speeds as observed in the past 28 days.
Selects sites which:
have reported within the last 6 minutes
takes the last 1 months history
removes time periods with 0 vehicles
removes speeds over 70
calculates threshold nut removes it if lower than 2mph
produces
name of sensor, sampling rate, sensible alert threshold (seen as mean - (stdev*2))
'''


x=parking()

recentsites=[n[0] for n in x.allloops() if n[1]<120]
print recentsites
import sys
print len(recentsites)

from collections import defaultdict
res=[]
for site in recentsites:
	data=x.findhistoricdata(site)
	if len(data)>1:
		sdata=sorted(data)
		this =[site, sorted([(sdata[n+1]-sdata[n]).total_seconds() for n in range(len(sdata)-1)])[int(len(sdata)*0.85)]]
		if this[1]>90000:
			continue
		dat=sorted([data[n] for n in data])
		this.append(int(np.mean(dat)+(4*np.std(dat))))
		if this[2]<=2 or this[2]>2500:
			continue
		print this
		res.append(this)
	

	
	j=defaultdict(int)
	'''
	for n in dat:
		j[int(n)]+=1
	plt.plot([n for n in sorted(j)],[j[m] for m in sorted(j)])
	plt.show()
	'''

with open('parking_thresholds.json','w') as jsonfile:
	json.dump(res,jsonfile)
