from flask import Flask

app=Flask(__name__,static_url_path="/static")

@app.route("/")
def helloworld():
	return ('hello')
