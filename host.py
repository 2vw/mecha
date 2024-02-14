import flask
from flask import (
    Flask,
    render_template,
    redirect,
    make_response,
    send_from_directory,
    request
)

from flask_sitemap import Sitemap
from threading import Thread
import logging



app = Flask(__name__, '/static')
ext = Sitemap(app=app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

servers=78
users=9074

@ext.register_generator
def index():
    """
    A function that serves as a generator for the 'index' endpoint.
    """
    # Not needed if you set SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS=True
    yield 'index', {}

@app.route('/')
def home():
    return render_template("index.html", servers=servers, users=users) # fill ths out eventually, just update it whenever you're bored enough for not hard work to do :)

@app.route('/login')
def login():
    return render_template("index.html", servers=servers, users=users)

@app.route('/register')
def register():
    return render_template("index.html", servers=servers, users=users)

@app.route('/dashboard')
def dashboard():
    return render_template("index.html", servers=servers, users=users)

@app.route('/terms')
def terms():
    return render_template("index.html", servers=servers, users=users)

@app.route('/privacy')
def privacy():
    return render_template("index.html", servers=servers, users=users)

@app.route('/support')
def support():
    return render_template("index.html", servers=servers, users=users)

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