
import helpers

def update():
	n=helpers.crequests()
	a=n.ALGET("UTMC Parking")
	print a[:3000]
	for n in json.loads(str(a))['Parking']['Carpark']:
		pass
				
update()
