import re, requests, json, urllib, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
from time import sleep
from datetime import date, datetime
from kivy.config import ConfigParser
from kivy.utils import platform
from tvsp2xmltv import defaults
from tvsp2xmltv import tvsGrabber
from flask import Flask, request, render_template, make_response, redirect, abort, send_from_directory
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from multiprocessing import Process, Queue
from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient
if platform == 'android':
    from jnius import autoclass

_root = os.path.dirname(os.path.abspath(__file__))
db = os.path.join(_root, 'database.db')
_path = os.path.join(_root, 'files')
json_file = os.path.join(_path, 'data.json')
conf = os.path.join(_root, 'main.ini')
config = ConfigParser()
config.read(conf)
sPort = int(config.get('Main', 'osc_port'))
if platform == 'android':
    PythonService = autoclass('org.kivy.android.PythonService')
    PythonService.mService.setAutoRestartService(True)

CLIENT = OSCClient('localhost', sPort)

stopped = False
global p1, p2, p3, p4, p5, p6, p7
p1 = p2 = p3 = p4 = p5 = p6 = p7 = None

def sig():
    Logger('[PROCESS][SIG::] starting ...')
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
    Logger('[PROCESS][SIG::] Done!')
    
def loop_sig():
    while True:
        now = int(time.time())
        last = int(config.get('Loop', 'sig'))
        if now > last + 1200:
            sig()
            config.set('Loop', 'sig', now)
            config.write()
        else:
            Logger('[LOOP][SIG::] sleeping for %s sec...' % str(last + 1200 - now))
            time.sleep(int(last + 1200 - now))
    pass

def m3u8():
    hurl = str(config.get('Main', 'm3u8_host')) + ':' + str(config.get('Main', 'flask_port'))
    Logger('[PROCESS][M3U8::] starting with url: %s ...' % str(hurl))
    #url = 'https://www2.vavoo.to/live2/index'
    matches1 = ["13TH", "AXN", "A&E", "INVESTIGATION", "TNT", "DISNEY", "SKY", "WARNER"]
    matches2 = ["BUNDESLIGA", "SPORT", "TELEKOM"]
    matches3 = ["CINE", "EAGLE", "KINO", "FILMAX", "POPCORN"]
    groups = []

    con = sqlite3.connect(db)
    cur = con.cursor()

    ssl._create_default_https_context = ssl._create_unverified_context
    req = Request('https://www2.vavoo.to/live2/index?output=json', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36'})
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    response = urlopen(req)
    content = response.read().decode('utf8')
    channel = json.loads(content)

    for c in channel:
        url = c['url']
        group = c['group']
        if c['group'] not in groups:
            groups.append(c['group'])
        if c['group'] == 'Germany':
            if any(x in c['name'] for x in matches1):
                group = 'Sky'
            if any(x in c['name'] for x in matches2):
                group = 'Sport'
            if any(x in c['name'] for x in matches3):
                group = 'Cine'
        cur.execute('SELECT * FROM channel WHERE name="' + c['name'].encode('ascii', 'ignore').decode('ascii') + '" AND grp="' + group + '"')
        test = cur.fetchone()
        if not test:
            name = re.sub('( (AUSTRIA|AT|HEVC|RAW|SD|HD|FHD|UHD|H265|GERMANY|DEUTSCHLAND|1080|DE|S-ANHALT|SACHSEN|MATCH TIME))|(\\+)|( \\(BACKUP\\))|\\(BACKUP\\)|( \\([\\w ]+\\))|\\([\\d+]\\)', '', c['name'].encode('ascii', 'ignore').decode('ascii'))
            logo = c['logo']
            tid = ''
            if c['group'] == 'Germany':
                cur.execute('SELECT * FROM tvs WHERE name="' + name + '" OR name1="' + name + '" OR name2="' + name + '" OR name3="' + name + '" OR name4="' + name + '"')
                test = cur.fetchone()
                if test:
                    tid = test[0]
                    logo = test[2]
            cur.execute('INSERT INTO channel VALUES(NULL,"' + c['name'].encode('ascii', 'ignore').decode('ascii') + '","' + group + '","' + logo + '","' + tid + '","' + c['url'] + '","' + name + '")')
        else:
            cur.execute('UPDATE channel SET url="' + c['url'] + '" WHERE name="' + c['name'].encode('ascii', 'ignore').decode('ascii') + '" AND grp="' + group + '"')
    con.commit()

    for group in groups:
        if os.path.exists("%s/%s.m3u8" % (_path, group)):
            os.remove("%s/%s.m3u8" % (_path, group))
        Send(b'/log', 'creating %s.m3u8 ...' % str(group))
        tf = open("%s/%s.m3u8" % (_path, group), "w")
        tf.write("#EXTM3U")
        tf.close()

    for c in channel:
        group = c['group']
        if c['group'] not in groups:
            groups.append(c['group'])
        if c['group'] == 'Germany':
            if any(x in c['name'] for x in matches1):
                group = 'Sky'
            if any(x in c['name'] for x in matches2):
                group = 'Sport'
            if any(x in c['name'] for x in matches3):
                group = 'Cine'
        cur.execute('SELECT * FROM channel WHERE name="' + c['name'].encode('ascii', 'ignore').decode('ascii') + '" AND grp="' + group + '"')
        row = cur.fetchone()
        if row:
            tf = open("%s/%s.m3u8" % (_path, c['group']), "a")
            if not str(row[3]) == '' and not str(row[4]) == '':
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s" tvg-logo="%s" tvg-id="%s",%s' % (row[1], row[2], row[3], row[4], row[6]))
            elif not str(row[3]) == '' and str(row[4]) == '':
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s" tvg-logo="%s",%s' % (row[1], row[2], row[3], row[6]))
            elif not str(row[4]) == '' and  str(row[3]) == '':
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s" tvg-id="%s",%s' % (row[1], row[2], row[4], row[6]))
            else:
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s",%s' % (row[1], row[2], row[6]))
            tf.write('\n#EXTVLCOPT:http-user-agent=VAVOO/2.6')
            tf.write('\n%s/%s' % (hurl, row[0]))
            tf.close()
        else:
            Logger('[PROCESS][M3U8::] Error!')
    con.close()
    Logger('[PROCESS][M3U8::] Done!')

def loop_m3u8():
    while True:
        now = int(time.time())
        last = int(config.get('Loop', 'm3u8'))
        sleep = int(config.get('Main', 'm3u8_sleep'))
        if now > last + sleep * 60 * 60:
            m3u8()
            config.set('Loop', 'm3u8', now)
            config.write()
        else:
            Logger('[LOOP][M3U8::] sleeping for %s sec...' % str(last + sleep * 60 * 60 - now))
            time.sleep(int(last + sleep * 60 * 60 - now))
    pass

def start_flask():
    flask_app = Flask(__name__)
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
    Logger('[PROCESS][FLASK::] starting Server on Host: %s, Port: %s ...' % (str(_host), str(_port)))
    flask_app.run(host=_host, port=_port, threaded=True)

def epg():
    Logger('[PROCESS][EPG::] starting ...')
    epg_grab = int(config.get('Main', 'epg_grab'))
    epg_channels = [ "123.tv", "13th Street Universal", "3sat", "Animal Planet", "ANIXE", "ARD alpha", "ARTE", "Auto Motor Sport", "AXN", "Bibel TV", "Bloomberg Europe TV", "BR", "Cartoon Network", "Classica", "Comedy Central", "CRIME + INVESTIGATION", "Das Erste", "DAZN", "DELUXE MUSIC", "Deutsches Musik Fernsehen", "Discovery HD", "Disney Channel", "DMAX", "Eurosport 1", "Eurosport 2", "Fix &amp; Foxi", "Health TV", "Heimatkanal", "History HD", "HR", "HSE24", "Jukebox", "kabel eins", "kabel eins classics", "kabel eins Doku", "KiKA", "KinoweltTV", "K-TV", "MDR", "Motorvision TV", "MTV", "N24 Doku", "Nat Geo HD", "NAT GEO WILD", "NDR", "nick", "Nick Jr.", "Nicktoons", "NITRO", "n-tv", "ONE", "ORF 1", "ORF 2", "ORF III", "ORF SPORT +", "PHOENIX", "ProSieben", "ProSieben Fun", "ProSieben MAXX", "Romance TV", "RTL", "RTL Crime", "RTL II", "RTL Living", "RTL Passion", "RTLplus", "SAT.1", "SAT.1 emotions", "SAT.1 Gold", "ServusTV", "Silverline", "sixx", "Sky Action", "Sky Atlantic HD", "Sky Cinema Best Of", "Sky Cinema Classics", "Sky Cinema Fun", "Sky Cinema Premieren", "Sky Cinema Premieren +24", "Sky Cinema Special HD", "Sky Cinema Thriller", "Sky Comedy", "Sky Crime", "Sky Family", "Sky Krimi", "Sky One", "Sony Channel", "Spiegel Geschichte", "Spiegel TV Wissen", "SUPER RTL", "SWR/SR", "Syfy", "tagesschau24", "Tele 5", "TLC", "TNT Comedy", "TNT Film", "TNT Serie", "TOGGO plus", "Universal Channel HD", "VOX", "VOXup", "WDR", "ZDF", "ZDFinfo", "ZDFneo" ]
    
    defaults.destination_file = os.path.join(_path, 'epg.xml')
    defaults.client = CLIENT
    if os.path.exists(defaults.destination_file):
        os.remove(defaults.destination_file)
    grabber = tvsGrabber.TvsGrabber()
    grabber.grab_days = int(epg_grab)
    grabber.pictures = False
    for chan in epg_channels:
        grabber.add_channel(str(chan))
    Logger('[PROCESS][EPG::] start grabbing ...')
    grabber.start_grab()
    Logger('[PROCESS][EPG::] safe epg.xml.gz ...')
    grabber.save()
    
    Logger('[PROCESS][EPG::] Done!')

def loop_epg():
    while True:
        sleep = int(config.get('Main', 'epg_sleep'))
        now = int(time.time())
        last = int(config.get('Loop', 'epg'))
        if now > last + sleep * 24 * 60 * 60:
            epg()
            config.set('Loop', 'epg', now)
            config.write()
        else:
            Logger('[LOOP][EPG::] sleeping for %s sec...' % str(last + sleep * 24 * 60 * 60 - now))
            time.sleep(int(last + sleep * 24 * 60 * 60 - now))
    pass

def stop():
    global p1, p2, p3, p4, p5, p6, p7, stopped
    if p1:
        p1.join(timeout=0)
        if p1.is_alive():
            p1.terminate()
            p1 = None
            Logger('[LOOP][FLASK::] terminate ...')
    if p2:
        p2.join(timeout=0)
        if p2.is_alive():
            p2.terminate()
            p2 = None
            Logger('[LOOP][SIG::] terminate ...')
    if p3:
        p3.join(timeout=0)
        if p3.is_alive():
            p3.terminate()
            p3 = None
            Logger('[LOOP][M3U8::] terminate ...')
    if p4:
        p4.join(timeout=0)
        if p4.is_alive():
            p4.terminate()
            p4 = None
            Logger('[LOOP][EPG::] terminate ...')
    if p5:
        p5.join(timeout=0)
        if p5.is_alive():
            p5.terminate()
            p5 = None
            Logger('[PROCESS][EPG::] terminate ...')
    if p6:
        p6.join(timeout=0)
        if p6.is_alive():
            p6.terminate()
            p6 = None
            Logger('[PROCESS][M3U8::] terminate ...')
    if p7:
        p7.join(timeout=0)
        if p7.is_alive():
            p7.terminate()
            p7 = None
            Logger('[PROCESS][SIG::] terminate ...')
    if platform == 'android':
        set_auto_restart_service(False, True)
    stopped = True

def start_epg():
    global p5
    if p5:
        p5.join(timeout=0)
        if p5.is_alive():
            Logger('[PROCESS][EPG::] allready started ...')
            return
    Logger('[PROCESS][EPG::] grabber starting exclusive ...')
    p5 = Process(target=epg)
    p5.start()

def start_m3u8():
    global p6
    if p6:
        p6.join(timeout=0)
        if p6.is_alive():
            Logger('[PROCESS][M3U8::] allready started ...')
            return
    Logger('[PROCESS][M3U8::] creation starting exclusive ...')
    p6 = Process(target=m3u8)
    p6.start()

def start_sig():
    global p7
    if p7:
        p7.join(timeout=0)
        if p7.is_alive():
            Logger('[PROCESS][SIG::] allready started ...')
            return
    Logger('[PROCESS][SIG::] creation starting exclusive ...')
    p7 = Process(target=sig)
    p7.start()

#### messages to app
def Send(type, message):
    CLIENT.send_message(type, [message.encode('utf8'), ])

def Logger(msg):
    CLIENT.send_message(b'/echo', [msg.encode('utf8'), ])

def set_auto_restart_service(restart=True,restart2=False):
    from jnius import autoclass
    Service = autoclass('org.kivy.android.PythonService').mService
    Service.setAutoRestartService(restart)
    Service.stopForeground(restart2)

def handler():
    SERVER = OSCThreadServer()
    SERVER.listen('localhost', default=True)
    SERVER.bind(b'/kill', stop)
    SERVER.bind(b'/start_epg', start_epg)
    SERVER.bind(b'/start_m3u8', start_m3u8)
    SERVER.bind(b'/start_sig', start_sig)
    Send(b'/reg', str(SERVER.getaddress()[1]))
    if platform == 'android':
        set_auto_restart_service()
    global p1, p2, p3, p4
    p1 = Process(target=start_flask)
    p1.start()
    p2 = Process(target=loop_sig)
    p2.start()
    if int(config.get('Main', 'm3u8_service')) > 0:
        p3 = Process(target=loop_m3u8)
        p3.start()
    else:
        Logger('[LOOP][M3U8::] not started, because service are disabled ...')
    if int(config.get('Main', 'epg_service')) > 0:
        p4 = Process(target=loop_epg)
        p4.start()
    else:
        Logger('[LOOP][EPG::] not started, because service are disabled ...')

    while True:
        sleep(1)
        if stopped:
            break
    print('terminate_server')
    if platform == 'android':
        set_auto_restart_service(False, True)
    SERVER.terminate_server()
    sleep(0.1)
    SERVER.close()
    #if platform == 'android':
        #PythonService.mService.setAutoRestartService(False)

if __name__ == '__main__':
    handler()
