import requests
import andyconfig
import os
import sqlite3
import time
import datetime
import simplejson as json
import uuid

class crequests(): #requestscache
	def __init__(self):
		self.conn=sqlite3.connect(":memory:")
		self.c=self.conn.cursor()
		self.createdb()
		self.age=60
		
	def createdb(self):
		self.c.execute('''CREATE TABLE netcache (time int, name text, data text)''')
		self.conn.commit()
		
	def getageofnewest(self,name):
		self.c.execute('''SELECT MAX(time),name,data from netcache WHERE name=(?)''',(name,))
		return self.c.fetchone() 
	
	def adddata(self,data,name):
		self.c.execute('''DELETE FROM netcache WHERE name=(?)''',(name,))
		self.c.execute('''INSERT INTO netcache VALUES (?,?,?)''',(time.time(),name,data))
		
	def get(self,name):
		tm=self.getageofnewest(name)
		if tm[0]:
			if time.time()-tm[0]<self.age:
				return tm[2]
		print 'loading...'
		data=requests.get(name).content
		#check if valid
		self.adddata(data,name)
		return data

	def __del__(self):
		self.conn.close()
		
		
class incidentdatabase(): #requestscache
	def __init__(self):
		self.conn=sqlite3.connect(":memory:")
		self.c=self.conn.cursor()
		self.createdb()
		
	def createdb(self):
		self.c.execute('''CREATE TABLE incidents(uuid text,sensor text,starttime integer, endtime integer, severity text,info text, access text, source text)''')
		self.conn.commit()
		
		
	def add(self,incident):
		self.c.execute('''INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?)''',(incident['ID'],incident['Sensor'],incident['Timestamp'],-1,incident['severity'],incident['info'],incident['access'],incident['source']))
		self.conn.commit()
		
	def update(self,incident):
		self.c.execute('''UPDATE incidents SET severity=?,info=? WHERE uuid=?''',(incident['severity'],incident['info'],incident['ID']))
		self.conn.commit()
				
	def remove(self,incident):
		self.c.execute('''UPDATE incidents SET endtime=? WHERE uuid=?''',(int(time.time()),incident['ID']))
		self.conn.commit()
	
	def querylive(self):
		self.c.execute('''SELECT * from incidents WHERE endtime=?''',(-1,))
		return self.c.fetchall()
		
	def querydate(self,start,end):
		self.c.execute('''SELECT * from incidents WHERE starttime>? and endtime<?''',(start,end))
		return self.c.fetchall()
	
	def __del__(self):
		self.conn.close()


class sensor():
	def __init__(self,ref,thresh,startdata=[0,0],database=None): #pass in the database pointer
		self.ref=ref
		self.thresh=thresh
		self.database=database
		self.incidents=[]
		self.current=False
		self.cdata=startdata
		self.incident={'severity':'Unknown','info':'No Further Info','access':'Private','source':'automated'}
		
	def main(self):
		self.update()
		self.exceeded()
	
	def current(self):
		return self.incidents
		
		
	def exceeded(self):
		if self.current:
			if self.test():
				self.updateincident()
				return
			else:
				self.current=False
				self.removeincident()
				return
		else:
			if self.test():
				self.createincident()
				self.current=True
	
	def test(self):
		#update any class variables here
		return False
		
	def createincident(self):
		self.incidents={'Sensor':self.ref,'ID':str(uuid.uuid1()),'Timestamp':int(time.time()),'severity':self.incident['severity'],'info':self.incident['info'],'access':self.incident['access'],'source':self.incident['source']}
		self.database.add(self.incidents)
	
	def updateincident(self):
		self.database.update(self.incidents)
		
	
	def removeincident(self):
		#update incident ended field
		self.database.remove(self.incidents)
		self.incidents=""
		
	
	def ALGET(self,name):
		n=cache.get("http://bcc.opendata.onl/"+name+".json?ApiKey="+os.environ['ALKEY'])
		#chek it worked
		return n
		

		
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
		#print self.ref,self.thresh[0],self.cdata[0]
		if self.thresh[0]>self.cdata[0]:
			self.incident['severity']=str(max([n for n in range(len(self.thresh)) if self.thresh[n]>self.cdata[0]]))
			self.incident['info']="Unusually low speeds detected"
			self.incident['access']="Public"
			return True
		else:
			return False

class parking(sensor):		

	def update(self):
		a=self.ALGET("UTMC Parking")
		#print a[:3000]
		for n in json.loads(str(a))['Parking']['Carpark']:
			try:
				#print n['SCN']
				if n['SCN']['content']==self.ref:
					ret={'data':{'Occupancy':n['Occupancy']['Percent']},'Timestamp':datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")}
			except TypeError:
				continue
		self.cdata=[ret['data']['Occupancy'],ret['Timestamp']]

	def test(self):
		return self.thresh<self.cdata[0]


class vms(sensor):
	def update(self):
		a=self.ALGET("UTMC VMS")
		for n in json.loads(str(a))['VMS_State']['VMS']:
			if n['SCN']==self.ref:
				t=n['Message']['content'].replace("|","")
				t=" ".join(t.split())
				if t==self.cdata[0]:
					tm=self.cdata[1]
				else:
					tm=datetime.datetime.now()
				self.cdata=[t,tm] #datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")]
		#print self.cdata[0]
	
	def test(self):
		#test is whether the sensor has been updated within the last hour abd the message is longer than thresh (3) digits
		#print self.cdata[1]
		return len(self.cdata[0])>self.thresh and (datetime.datetime.now()-self.cdata[1]).total_seconds()<3600


cache=crequests()



import json
from Tkinter import *

root=Tk()
root.geometry("500x200")
var=StringVar()
label=Message(root,textvariable=var,relief=RAISED)
var.set("please wait")
label.pack(expand=True,fill=BOTH)

db=incidentdatabase()

sensors=[]

with open('rtem_thresholds.json','r') as jsonfile:
	rtems=json.load(jsonfile)
for x in rtems:
	sensors.append(rtem(x[0],x[2],database=db))

with open('parking_thresholds.json','r') as jsonfile:
	rtems=json.load(jsonfile)
for x in rtems:
	sensors.append(parking(x[0],95,database=db))


import vms as loadvms
for n in loadvms.main():
	sensors.append(vms(n[3],3,startdata=[" ".join((n[1].replace("|","")).split()),datetime.datetime.now()-datetime.timedelta(seconds=3601)],database=db))


while True:
	z=[]
	for x in sensors:
		x.main()
		if x.incidents:
			z.append(x.incidents)
	if z:
		m=""
		for x in z:
			#print x
			m+= "Sensor "+x['Sensor']+" "+x['severity']+"\n"
	else:
		m="Good Service"
	os.system('clear')
	print json.dumps(db.querylive(),indent=2)

	var.set(m)
	root.update()
	time.sleep(1)
