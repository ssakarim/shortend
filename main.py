from flask import Flask, Blueprint, render_template, request, redirect, Response
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

from datetime import datetime
import logging
import os
import string
from random import choices
from base62 import * 




app = Flask(__name__)

# Google Cloud SQL (change this accordingly)
DBUSR=os.environ.get('DB_USER', 'Specified environment variable is not set.')
PASSWORD =os.environ.get('DB_PASS', 'Specified environment variable is not set.')
DBNAME =os.environ.get('DB_NAME', 'Specified environment variable is not set.')
PROJECT_ID =os.environ.get('GCP_PROJECT', 'Specified environment variable is not set.')
INSTANCE_NAME =os.environ.get('myinstance', 'Specified environment variable is not set.')
CONNECTION_NAME=os.environ.get('CLOUD_SQL_CONNECTION_NAME', 'Specified environment variable is not set.')


# configuration
app.config["SECRET_KEY"] = randStr(N=30)
app.config["SQLALCHEMY_DATABASE_URI"]= f"mysql+pymysql://{DBUSR}:{PASSWORD}@/{DBNAME}?unix_socket=/cloudsql/{CONNECTION_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= True

db = SQLAlchemy(app)


@app.route('/<short_url>')
def redirect_to_url(short_url):
    link = Link.query.filter_by(short_url=short_url).first_or_404()
    link.visits = link.visits + 1
    db.session.commit()

    return redirect(link.original_url) 

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/add_link', methods=['POST'])
def add_link():
    original_url = request.form['original_url']
    link = Link(original_url=original_url)
    if link.query.filter_by(original_url=original_url).first():
        return render_template('duplicate.html', existing_url=link.short_url)
    else:
#        link = Link(original_url=original_url)
        db.session.add(link)
        db.session.commit()
        return render_template('link_added.html', 
            new_link=link.short_url, original_url=link.original_url)

@app.route('/stats')
def stats():
    links = Link.query.all()

    return render_template('stats.html', links=links)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def randStr(chars = string.ascii_uppercase + string.digits, N=10):
	return ''.join(random.choice(chars) for _ in range(N))

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable = False)
    original_url = db.Column(db.String(512), nullable = False)
    short_url = db.Column(db.String(7), unique=True, nullable = False)
    visits = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.short_url = self.generate_short_link()

    def generate_short_link(self):
        short_url=encode(bytes_to_int(self.original_url.encode('ascii')))[0:7]
        link = self.query.filter_by(short_url=short_url).first()
        #if link:
        #    return self.generate_short_link()
        return short_url

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

