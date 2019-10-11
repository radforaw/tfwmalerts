
from waitress import serve
from alertapi import *

if __name__=='__main__':
	serve(app,listen='0.0.0.0:80') #urlscheme https
