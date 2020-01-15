import andyconfig
import os
import requests
import json
import datetime
import matplotlib.pyplot as plt
print os.environ['ALKEY']
import numpy as np
from helpers import *
from collections import defaultdict
import json
import math

period=56

class RTEM():
	def __init__(self):
		
		n=requests.get("http://bcc.opendata.onl/UTMC RTEM.json?ApiKey="+os.environ['ALKEY'])
		self.data=n.json()
		
	def allloops(self):
		ret=[]
		for n in self.data['RTEMS']['kids']:
			ret.append([self.data['RTEMS']['kids'][n]['kids']['SCN']['value'], int((datetime.datetime.now()-datetime.datetime.strptime(self.data['RTEMS']['kids'][n]['kids']['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)])
		return ret
		
	
	def allsites(self):
		ret=set()
		for n in self.data['RTEMS']['kids']:
			ret.add(self.data['RTEMS']['kids'][n]['kids']['SCN']['attrs']['Site'])
		return ret
	
	def findcurrentdata(self,site,removezeroes=False):
		ret=[]
		for n in self.data['RTEMS']['kids']:
			b=self.data['RTEMS']['kids'][n]['kids']
			if int(b['SCN']['attrs']['Site'])==site:
				if removezeroes:
					if float(b['Speed'])+float(b['Cars'])+float(b['Trailers'])+float(b['Rigids'])+float(b['Buses'])==0:
						continue
				ret.append([b['SCN']['value'], float(b['Speed']),float(b['Cars']),float(b['Trailers'])+float(b['Rigids'])+float(b['Buses']), int((datetime.datetime.now()-datetime.datetime.strptime(b['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60),b['Date']])
		return ret
						
	def findhistoricdata(self,site,end=str((datetime.datetime.now()+datetime.timedelta(days=1)).date()),start=str(datetime.datetime.now().date()-datetime.timedelta(days=0)),removezeroes=False):
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
		d={datetime.datetime.strptime(a['Date'],"%Y-%m-%d %H:%M:%S"):a for a in tmp}	
		return d
		
	def findhistoricdata(self,site,end=str((datetime.datetime.now()+datetime.timedelta(days=1)).date()),start=str(datetime.datetime.now().date()-datetime.timedelta(days=28)),removezeroes=False):
		url="http://bcc.opendata.onl/UTMC RTEM.json?"+"SCN="+str(site)+"&TS=true&Earliest="+start+"&Latest="+end+"&ApiKey="+os.environ['ALKEY']
		n=requests.get(url)
		res=n.json()
		data=[]
		names=[]
		for n in res['RTEMs']['kids']:
			b=res['RTEMs']['kids'][n]['kids']
			names.append(b['SCN']['value'])
			data.append(b)
		d=data
		d={datetime.datetime.strptime(d[a]['Date'],"%Y-%m-%d %H:%M:%S"):d[a] for a in range(len(d))}	
		#print d
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



calculate standard error
sqaure root of sample size
confidence inveral of standard error

'''

def createthresholds():
	x=RTEM()
	recentsites=[n[0] for n in x.allloops() if n[1]<6 ]
	res=[]
	for site in recentsites:
		print site
		data=x.findhistoricdata(site)
		if len(data)>1:
			sdata=sorted(data)
			this =[site, sorted([(sdata[n+1]-sdata[n]).total_seconds() for n in range(len(sdata)-1)])[int(len(sdata)*0.85)]]
			if this[1]>9000:
				print ('not enought records - '+str(this[1]))
				continue
			dat=sorted([float(data[n]['Speed']) for n in data if 130>float(data[n]['Speed'])>0])
			if len(dat)==0:
				print ('all zeroes')
				continue
			l,m=np.mean(dat),np.std(dat)
			#print ('standard error',len(dat),m,l,l-((m/(math.sqrt(len(dat)))*4)),l+((m/math.sqrt(len(dat)))*4))
			this.append([int(l-(2*m)),int(l-(3*m)),int(l-(4*m))])
			if this[2][0]<=2:
				print ('threshold lower than 2 mph')
				continue
			print this
			res.append(this)
	with open('helpers/rtem_thresholds.json','w') as jsonfile:
		json.dump(res,jsonfile)
		
class rtem(sensor):		

	def update(self):
		a=self.ALGET("UTMC RTEM")
		#print a[:3000]
		for n in json.loads(str(a))['RTEMS']['RTEM']:
			if n['SCN']['content']==self.ref:
				ret={'data':{'Speed':n['Speed'],'Vehicles':n['Vehicles'],'Occupancy':n['Occupancy']},'Timestamp':datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")}
		if ret['data']['Vehicles']!=0:		
			self.cdata=[ret['data']['Speed'],ret['Timestamp']]

	def test(self):
		#test is whether speed is lower than threshold, currently 2 SD away from mean
		print self.ref,self.thresh[0],self.cdata[0]
		if self.thresh[0]>self.cdata[0]:
			self.incident['severity']=str(max([n for n in range(len(self.thresh)) if self.thresh[n]>self.cdata[0]]))
			self.incident['info']="Unusually low speeds detected"
			self.incident['access']="Public"
			return True
		else:
			return False
