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
		data=requests.get(name).content
		#check if valid
		self.adddata(data,name)
		return data

	def __del__(self):
		self.conn.close()


class sensor():
	def __init__(self,ref,thresh):
		self.ref=ref
		#self.struct={"ID":None}
		self.thresh=thresh
		self.incidents=[]
		self.current=False
		self.cdata=[0,0]
		
	def main(self):
		self.update()
		self.exceeded()
	
	def current(self):
		return self.incidents
		
	def database(self):
		pass
		
	def exceeded(self):
		if self.current:
			if self.test():
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
		return False
		
	def createincident(self,severity='Unknown',info='No Further Info',access='Private',source='automated'):
		self.incidents.append({'ID':uuid.uuid1(),'Timestamp':time.time(),'Sensor':self.ref,'Severity':severity,'Description':info,'Access':access,'Source':source})
	
	def removeincident(self):
		self.incidents=[]
	
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
		return self.thresh>self.cdata[0]

class vms(sensor):
	def update(self):
		a=self.ALGET("UTMC VMS")
		for n in json.loads(str(a))['VMS_State']['VMS']:
			if n['SCN']==self.ref:
				t=n['Message']['content'].replace("|","")
				t=" ".join(t.split())
				self.cdata=[t,datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")]
		print self.cdata[0]
	
	def test(self):
		return len(self.cdata[0])>self.thresh


cache=crequests()



import json
from Tkinter import *

root=Tk()
root.geometry("500x200")
var=StringVar()
label=Message(root,textvariable=var,relief=RAISED)
var.set("please wait")
label.pack(expand=True,fill='both')



sensors=[]

with open('rtem_thresholds.json','r') as jsonfile:
	rtems=json.load(jsonfile)
for x in rtems:
	sensors.append(rtem(x[0],x[2]))

sensors.append(vms('M0004',3))


while True:
	z=[]
	for x in sensors:
		x.main()
		if x.incidents:
			z.append(x.incidents)
		time.sleep(.1)
	if z:
		m=""
		for x in z:
			print x
			m+= "Sensor "+x[0]['Sensor']+"\n"
	else:
		m="Good Service"
	var.set(m)
	root.update()
