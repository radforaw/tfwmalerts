import sqlite3
import requests
import time
import os
import uuid
import sys
	
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
		try:
			data=requests.get(name,timeout=5).content
		except:
			if tm[0]:
				return tm[2]
			print 'got no live or historic data'
			sys.exit(0)
		#check if valid
		self.adddata(data,name)
		return data

	def __del__(self):
		self.conn.close()
		
	
class sensor():
	
	cache=crequests()
	
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
		n=sensor.cache.get("http://bcc.opendata.onl/"+name+".json?ApiKey="+os.environ['ALKEY'])
		#chek it worked
		return n
		

		
class incidentdatabase(): #requestscache
	def __init__(self,fileloc=":memory:"):
		self.conn=sqlite3.connect(fileloc)
		self.c=self.conn.cursor()
		try:
			self.createdb()
		except:
			pass
		
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
