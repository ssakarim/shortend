from flask import Flask, Blueprint, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
import logging
import os
import string
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

#Local Testing
#cloud_sql_proxy -instances==CLOUD_SQL_CONNECTION_NAMEtcp:3306
#PUBLIC_IP_ADDRESS ="127.0.0.1"
#app.config["SQLALCHEMY_DATABASE_URI"]= f"mysql+pymysql://root:{PASSWORD}@{PUBLIC_IP_ADDRESS}:3306/{DBNAME}"

db = SQLAlchemy(app)


@app.route('/<short_url>')
def redirect_to_url(short_url):
    link = Link.query.filter_by(short_url=short_url).first_or_404()
    link.visits = link.visits + 1
    db.session.commit()
    return redirect(link.original_url) 

@app.route('/')
def index():
    links = Link.query.all()
    return render_template('index.html', codes=links) 

@app.route('/add_link', methods=['GET','POST'])
def add_link():
    if request.method == "POST":
        original_url = request.form['original_url']
        if not validate_url(request.form['original_url']):
            return render_template('invalid_url.html', original_url=original_url)
        link = Link(original_url=original_url)
        if link.query.filter_by(short_url=link.short_url).first():
            return render_template('duplicate.html', existing_url=link.short_url)
        else:
            db.session.add(link)
            db.session.commit()
            return render_template('link_added.html', new_link=link.short_url, original_url=link.original_url, host_url=request.host_url)
    else:
        return redirect(url_for('index'))

@app.route('/stats')
def stats():
    url = []
    v = []
    links = Link.query.all()
    for l in links:
        url.append(l.short_url)
        v.append(l.visits)
    fig, ax = plt.subplots(figsize=(10,4), linewidth=5, edgecolor='.5')
    x = np.arange(len(url))
    ax.bar(x, v,0.35, facecolor='.5', alpha=.3, label='URL Shortner')
    ax.set_title('Visits Frequency')
    ax.set_ylabel('# of visits')
    ax.set_xticks(x)
    ax.set_xticklabels(url)
    ax.legend()
    plt.savefig('static/statsplot.png')
    plt.show()
    plt.clf()
    plt.cla()
    plt.close()
    return render_template('stats.html', links=links)

@app.route('/<short_url>/stats')
def url_stats(short_url):
    link = Link.query.filter_by(short_url=short_url).first_or_404()
    return render_template('url_stats.html', link=link)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

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

