from flask import Flask, request, render_template, make_response, redirect, abort, send_from_directory
import re, requests, json, urllib, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from kivy.config import ConfigParser
from kivy.logger import Logger, LOG_LEVELS

Logger.setLevel(LOG_LEVELS["info"])

def start_flask():
    flask_app = Flask(__name__)
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(_rootdir, 'database.db')
    _path = os.path.join(_rootdir, 'files')
    conf = os.path.join(_rootdir, 'main.ini')
    config = ConfigParser()
    config.read(conf)
    _host = str(config.get('Main', 'flask_host'))
    _port = int(config.get('Main', 'flask_port'))

    @flask_app.route('/')
    def hello():
        return 'Hello, World!'

    @flask_app.route('/<int:stream_id>')
    def show_stream(stream_id):
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute('SELECT * FROM channel WHERE id="' + str(stream_id) + '"')
        row = cur.fetchone()
        if row:
            url = str(row[5])
            cur.execute('SELECT * FROM sig')
            row = cur.fetchone()
            sig = str(row[0])
            link = url + '?n=1&b=5&vavoo_auth=' + sig

            return redirect(link), 302
        else:
            abort(404)

    @flask_app.route('/<path:path>')
    def show_m3u8(path):
        try:
            return send_from_directory('%s' % _path, path, as_attachment=True)
        except FileNotFoundError:
            abort(404)

    flask_app.run(host=_host, port=_port, threaded=True)


if __name__ == "__main__":
    start_flask()
