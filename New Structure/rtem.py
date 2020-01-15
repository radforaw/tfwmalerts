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
from bccdatasets import RTEM

period=56
'''
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
'''

def createthresholds(last=6):
	'''Creates speed thresholds based on the data
	
	The aim is to identify abnormally low speeds as observed in the past 28 days.
	Selects sites which:
		have reported within the last (last=6) minutes
		takes the last 1 months history
		removes time periods with 0 vehicles
		removes speeds over 70
		calculates threshold nut removes it if lower than 2mph
		produces
		name of sensor, sampling rate, sensible alert threshold (seen as mean - (stdev*2))
	'''
	
	x=RTEM()
	recentsites=[n[0] for n in x.allloops() if n[1]<last]
	res=[]
	for site in recentsites:
		try:
			data=x.findhistoricdata(site,str(datetime.datetime.now().date()),str((datetime.datetime.now()-datetime.timedelta(days=period)).date()))
			
		except KeyError:
			continue
		if len(data)>1:
			sdata=sorted(data)
			this =[site, sorted([(sdata[n+1]-sdata[n]).total_seconds() for n in range(len(sdata)-1)])[int(len(sdata)*0.85)]]
			if this[1]>9000:
				continue
			dat=sorted([data[n]['Speed'] for n in data if data[n]['Speed']>0])
			l,m=np.mean(dat),np.std(dat)
			this.append([int(l-(2*m)),int(l-(3*m)),int(l-(4*m))])
			if this[2][0]<=2:
				continue
			print this
			res.append(this)
	with open('rtem_thresholds.json','w') as jsonfile:
		json.dump(res,jsonfile,sort_keys=True,indent=2)
		
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

if __name__=='__main__':
	createthresholds()
