import flask
from flask import (
    Flask,
    render_template,
    redirect,
    make_response
)

from host import Flask
from threading import Thread
import logging

app = Flask(__name__, '/flask/static')
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return render_template("index.html", servers=78, users=9074) # fill ths out eventually, just update it whenever you're bored enough for not hard work to do :)

def run():
  """
  This function runs the application on the specified host and port.
  """
  app.run(host='0.0.0.0',port=8080)

def alive():  
    """
    A function designed to start a new thread to run the function. So it can do its thing alongside the main program.
    """
    t = Thread(target=run) # oh my god really?!?!?!!??
    t.start()
    
# if this ends up working im pushing the changes idgaf anymore :)