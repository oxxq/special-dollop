import re, requests, json, urllib, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
from datetime import date, datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from kivy.config import ConfigParser
from kivy.logger import Logger, LOG_LEVELS

Logger.setLevel(LOG_LEVELS["info"])

def sig():
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(_rootdir, 'database.db')
    _path = os.path.join(_rootdir, 'files')
    json_file = os.path.join(_path, 'data.json')
    Logger.info('starting sig process ...')
    if not os.path.exists(json_file):
        veclist = requests.get("https://raw.githubusercontent.com/michaz1988/michaz1988.github.io/master/data.json").json()
        vecs = { 'time': int(time.time()), 'vecs': veclist }
        with open(json_file, "w") as k:
            json.dump(vecs, k, indent=2)
    else:
        with open(json_file) as k:
            vecs = json.load(k)
    try:
        if 'vecs' in vecs:
            sig = None
            i = 0
            while (not sig and i < 50):
                i+=1
                vec = {"vec": random.choice(vecs['vecs'])}
                req = requests.post('https://www.vavoo.tv/api/box/ping2', data=vec).json()
                if req.get('signed'):
                    sig = req['signed']
                elif req.get('data', {}).get('signed'):
                    sig = req['data']['signed']
                elif req.get('response', {}).get('signed'):
                    sig = req['response']['signed']

            stime = int(time.time())
            con = sqlite3.connect(db)
            cur = con.cursor()
            cur.execute('DELETE FROM sig')
            cur.execute('INSERT INTO sig VALUES("' + sig + '","' + str(stime) + '")')
            con.commit()
            con.close()
    except Exception  as e:
        raise
    Logger.info('sig process Done!')
    
def loop_sig():
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    cconf = os.path.join(_rootdir, 'sig_service.ini')
    cconfig = ConfigParser()
    cconfig.read(cconf)
    if not os.path.exists(cconf):
        cconfig.setdefaults('Loop', {'time': 0})
        cconfig.write()
    while True:
        now = int(time.time())
        last = int(cconfig.get('Loop', 'time'))
        if now > last + 600:
            sig()
            cconfig.set('Loop', 'time', now)
            cconfig.write()
        else:
            Logger.info('sig loop sleeping for %s sec...' % str(last + 600 - now))
            time.sleep(int(last + 600 - now))
    pass

if __name__ == "__main__":
    loop_sig()
