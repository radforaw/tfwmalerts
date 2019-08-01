import requests
import datetime
import pyproj as proj
import andyconfig
import os
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
		
if __name__=="__main__":
	print get_vms()
