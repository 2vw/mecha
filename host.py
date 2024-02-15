import flask, json
from flask import (
    Flask,
    render_template,
    redirect,
    make_response,
    send_from_directory,
    request
)

from threading import Thread
import logging

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

with open("json/config.json", "r") as f:
  config = json.load(f)

DBclient = MongoClient(config['MONGOURI'], server_api=ServerApi('1'))

db = DBclient['beta']
userdb = db['users']
serverdb = db['servers']
settingsdb = db['settings']

app = Flask(__name__, '/static')
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
    

@app.route('/')
def home():
    data = settingsdb.find_one({'_id': 1, "setting": "stats"})
    return render_template("index.html", servers=data["servers"], users=data["users"]) 

@app.route('/login')
def login():
    data = settingsdb.find_one({'_id': 1, "setting": "stats"})
    return render_template("index.html", servers=data["servers"], users=data["users"])

@app.route('/register')
def register():
    data = settingsdb.find_one({'_id': 1, "setting": "stats"})
    return render_template("index.html", servers=data["servers"], users=data["users"])

@app.route('/dashboard')
def dashboard():
    data = settingsdb.find_one({'_id': 1, "setting": "stats"})
    return render_template("index.html", servers=data["servers"], users=data["users"])

@app.route('/terms')
def terms():
    data = settingsdb.find_one({'_id': 1, "setting": "stats"})
    return render_template("index.html", servers=data["servers"], users=data["users"])

@app.route('/privacy')
def privacy():
    data = settingsdb.find_one({'_id': 1, "setting": "stats"})
    return render_template("index.html", servers=data["servers"], users=data["users"])

@app.route('/support')
def support():
    data = settingsdb.find_one({'_id': 1, "setting": "stats"})
    return render_template("index.html", servers=data["servers"], users=data["users"])

# creating the routes for sitemaps to be made so thats why they're useless right now :)

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

def run():
  """
  This function runs the application on the specified host and port.
  """
  app.run(host='0.0.0.0', port=3000)

def alive():  
    """
    A function designed to start a new thread to run the function. So it can do its thing alongside the main program.
    """
    t = Thread(target=run) # oh my god really?!?!?!!??
    t.start()
    
# if this ends up working im pushing the changes idgaf anymore :)