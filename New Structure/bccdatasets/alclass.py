#!python3
import andyconfig
import os
import requests
import datetime




#print os.environ['ALKEY']


class RTEM():
	def __init__(self):
		
		n=requests.get("http://bcc.opendata.onl/UTMC RTEM.json?ApiKey="+os.environ['ALKEY'])
		self.data=n.json()
		print (n.content[:1000])
	
	def sites_get(self):
		ret=set()
		for n in self.data['RTEMS']['kids']:
			ret.add(self.data['RTEMS']['kids'][n]['kids']['SCN']['value'])
		return ret
		
	def allloops(self):
		ret=[]
		for n in self.data['RTEMS']['kids']:
			ret.append([self.data['RTEMS']['kids'][n]['kids']['SCN']['value'],(datetime.datetime.now()-datetime.datetime.strptime(self.data['RTEMS']['kids'][n]['kids']['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60])
		return ret
		
	'''	return [[n['SCN']['content'], int((datetime.datetime.now()-datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)] for n in self.data['RTEMS']['RTEM']]
	'''
	
	def locs_get(self):
		ret={}
		for n in self.data['RTEMS']['kids']:
			print (n)
			try:
				ret[self.data['RTEMS']['kids'][n]['kids']['SCN']['value']]=self.data['RTEMS']['kids'][n]['kids']['Description']
			except:
				ret[self.data['RTEMS']['kids'][n]['kids']['SCN']['value']]='No Description'
		return ret
	
	def findcurrentdata(self,site,removezeroes=False):
		ret=[]
		for n in self.data['RTEMS']['RTEM']:
			if n['SCN']['Site']==site:
				if removezeroes:
					if n['Speed']+n['Cars']+n['Trailers']+n['Rigids']+n['Buses']==0:
						continue
				ret.append([n['SCN']['content'], n['Speed'],n['Cars']+n['Trailers']+n['Rigids']+n['Buses'], int((datetime.datetime.now()-datetime.datetime.strptime(n['Date'],"%Y-%m-%d %H:%M:%S")).total_seconds()/60)])
		return ret

	def findhistoricdata(self,site,end,start,removezerors=0): #end=str((datetime.datetime.now()+datetime.timedelta(days=1)).date()),start=str(datetime.datetime.now().date()-datetime.timedelta(days=1)),removezeroes=False):
		url="http://bcc.opendata.onl/UTMC RTEM.json?"+"SCN="+str(site)+"&TS=true&Earliest="+start+"&Latest="+end+"&ApiKey="+os.environ['ALKEY']
		print (url,end,start)
		
		n=requests.get(url)
		res=n.json()
		print (n.content[:1000])
		#print (res['RTEMs']['kids'])
		data=[]
		for n in res['RTEMs']['kids']:
			data.append(res['RTEMs']['kids'][n]['kids'])
			'''
			except TypeError:
				data.append(res['RTEMs']['kids'][n]['kids'])
			'''
			
		#print ('55555',data[0])
		
		d={}
		for a in data:
			tmp={}
			for t in a:
				try:
					tmp[t]=float(a[t])
				except (TypeError,ValueError) as e:
					tmp[t]=a[t]
				
			d[datetime.datetime.strptime(a['Date'],"%Y-%m-%d %H:%M:%S")]=tmp
		return d
		
if __name__=='__main__':
	x=RTEM()
	print (x.locs_get())
	d=list(x.sites_get())[1]
	a=(x.findhistoricdata('R0199D1L0'))
