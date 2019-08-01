import andyconfig
import os
import requests
import json
import datetime
import matplotlib.pyplot as plt
print os.environ['ALKEY']
import numpy as np

period=56

class RTEM():
	def __init__(self):
		
		n=requests.get("http://bcc.opendata.onl/UTMC RTEM.json?ApiKey="+os.environ['ALKEY'])
		self.data=n.json()
		
	
	def allsites(self):
		return [n['SCN']['Site'] for n in self.data['RTEMS']['RTEM']]
		
	def allloops(self):
		return [[n['SCN']['content'], int((datetime.datetime.now()-datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)] for n in self.data['RTEMS']['RTEM']]
		
	def findcurrentdata(self,site,removezeroes=False):
		ret=[]
		for n in self.data['RTEMS']['RTEM']:
			if n['SCN']['Site']==site:
				if removezeroes:
					if n['Speed']+n['Cars']+n['Trailers']+n['Rigids']+n['Buses']+n['Motorbikes']==0:
						continue
				ret.append([n['Speed'],n['Cars']+n['Trailers']+n['Rigids']+n['Buses']+n['Motorbikes'], int((datetime.datetime.now()-datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)])
		return ret

						
	def findhistoricdata(self,site,start=str((datetime.datetime.now()-datetime.timedelta(days=period)).date()),end=str(datetime.datetime.now().date()),removezeroes=False):
		url="http://bcc.opendata.onl/UTMC RTEM.json?"+"SCN="+str(site)+"&TS=true&Earliest="+start+"&Latest="+end+"&ApiKey="+os.environ['ALKEY']		
		n=requests.get(url)
		res=n.json()
		data=[]
		names=[]
		for n in res['RTEMs']['Data']:
			names.append(n)
			data.append(res['RTEMs']['Data'][n])
		d = [[data[j][i] for j in range(len(data))] for i in range(len(data[0]))]
		tmp=[]
		for n in d:
			tmp.append({names[a]:n[a] for a in range(len(data))})
		d={datetime.datetime.strptime(a['Date'],"%Y-%m-%d %H:%M:%S"):a for a in tmp if a['Vehicles']!=0 and a['Speed']<70}	
		return d
		

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


x=RTEM()

recentsites=[n[0] for n in x.allloops() if n[1]<6 ]
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
		if this[1]>9000:
			continue
		dat=sorted([data[n] for n in data])
		this.append(int(np.mean(dat)-(2*np.std(dat))))
		if this[2]<=2:
			continue
		print this
		res.append(this)
	
import json

with open('rtem_thresholds.json','w') as jsonfile:
	json.dump(res,jsonfile)
	
	#j=defaultdict(int)
	#for n in dat:
	#	j[n]+=1
	#plt.plot([n for n in sorted(j)],[j[m] for m in sorted(j)])
	#plt.show()
