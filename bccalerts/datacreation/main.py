import sys
print (sys.path)

import requests
import andyconfig
import os
import sqlite3
import time
import datetime
import simplejson as json
import uuid
from helpers import *
from rtemhelp import *
import parking
import vms as loadvms
#createthresholds()

import json

# eye candy from here
try:
	from Tkinter import *
	tkon=True
except ImportError:
	tkon=False



	
def looper():
	if tkon:
		root=Tk()
		root.geometry("500x200")
		var=StringVar()
		label=Message(root,textvariable=var,relief=RAISED)
		var.set("please wait")
		label.pack(expand=True,fill=BOTH)
	# to here


	db=incidentdatabase(fileloc='helpers/testincident.db')
	db.resetclean()

	sensors=[]

	# load rtem speed sensors
	with open('helpers/rtem_thresholds.json','r') as jsonfile:
		rtems=json.load(jsonfile)
	for x in rtems:
		sensors.append(rtem(x[0],x[2],database=db))

	# load parking sensors
	with open('helpers/parking_thresholds.json','r') as jsonfile:
		rtems=json.load(jsonfile)
	for x in rtems:
		sensors.append(parking.parking(x[0],95,database=db))

	# load vms thresholds (set 1 hr 1 second threhsold inline)
	for n in loadvms.main():
		sensors.append(loadvms.vms(n[3],3,startdata=[" ".join((n[1].replace("|","")).split()),datetime.datetime.now()-datetime.timedelta(seconds=3601)],database=db))


	while True:
		z=[]
		for x in sensors:
			x.main()
			if x.incidents:
				z.append(x.incidents)
		#all this is just eye candy
		if tkon:
			if z:
				m=""
				for x in z:
					m+= "Sensor "+x['Sensor']+" "+x['severity']+"\n"
			else:
				m="Good Service"
			os.system('clear') # this is to stop the CLI window getting too messy
			print (db.querylive())
	
			var.set(m)
			root.update()
		#up to here
		
		time.sleep(10)



if __name__=="main":
	looper()
