import requests
import datetime
import pyproj as proj
import andyconfig
import os
import json
from helpers import *
try:
	from lxml import etree as ET
except ImportError:
	import xml.etree.cElementTree as ET

def get_vms():
	crs_wgs=proj.Proj(init='epsg:4326')
	crs_bng=proj.Proj(init='epsg:27700')
	url='http://bcc.opendata.onl/UTMC VMS.xml'
	n=requests.get(url,params={'ApiKey':os.environ['ALKEY']})
	root=ET.fromstring(n.content)
	ret=[]
	#print (n.content)
	#print root('VMS_State')
	for VMS in root.iterfind('VMS'):
		tmp=datetime.datetime.strptime(VMS.find("Date").text,'%Y-%m-%d %H:%M:%S')
		now=datetime.datetime.now()-datetime.timedelta(days=356)
		if tmp>now and len(VMS.find('SCN').text)<20 and VMS.find('Message').text:
			ret.append([VMS.find('Description').text,VMS.find('Message').text,proj.transform(crs_bng,crs_wgs,(float(VMS.find('Easting').text)),(float(VMS.find('Northing').text))),VMS.find('SCN').text])
	return ret

def main():
	t=get_vms()
	return [b for b in t if b[3][:2]=='BI' or b[3][:2]=='M0' or b[0]=="Null"]
	
	
	
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

		
if __name__=="__main__":
	print get_vms()
