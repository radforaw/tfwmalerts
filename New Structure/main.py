import requests
import andyconfig
import os
import sqlite3
import time
import datetime
import simplejson as json
import uuid
from helpers import *
from rtem import *
import parking
import vms
createthresholds()

import json
from Tkinter import *

root=Tk()
root.geometry("500x200")
var=StringVar()
label=Message(root,textvariable=var,relief=RAISED)
var.set("please wait")
label.pack(expand=True,fill=BOTH)

db=incidentdatabase(fileloc='testincident.db')

sensors=[]

with open('rtem_thresholds.json','r') as jsonfile:
	rtems=json.load(jsonfile)
for x in rtems:
	sensors.append(rtem(x[0],x[2],database=db))

with open('parking_thresholds.json','r') as jsonfile:
	rtems=json.load(jsonfile)
for x in rtems:
	sensors.append(parking.parking(x[0],95,database=db))


import vms as loadvms
for n in loadvms.main():
	sensors.append(vms.vms(n[3],3,startdata=[" ".join((n[1].replace("|","")).split()),datetime.datetime.now()-datetime.timedelta(seconds=3601)],database=db))


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
	time.sleep(10)
