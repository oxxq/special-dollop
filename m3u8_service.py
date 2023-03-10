import re, requests, json, urllib, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
from datetime import date, datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from kivy.config import ConfigParser
from kivy.logger import Logger, LOG_LEVELS

Logger.setLevel(LOG_LEVELS["info"])

def m3u8():
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(_rootdir, 'database.db')
    _path = os.path.join(_rootdir, 'files')
    config = ConfigParser()
    config.read('main.ini')
    hurl = str(config.get('Main', 'm3u8_host')) + ':' + str(config.get('Main', 'flask_port'))
    Logger.info('starting m3u8 process ...')
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
            Logger.info('m3u8 process Error!')
    con.close()
    Logger.info('m3u8 process Done!')

def loop_m3u8():
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    cconf = os.path.join(_rootdir, 'm3u8_service.ini')
    cconfig = ConfigParser()
    cconfig.read(cconf)
    if not os.path.exists(cconf):
        cconfig.setdefaults('Loop', {'time': 0})
        cconfig.write()
    conf = os.path.join(_rootdir, 'main.ini')
    config = ConfigParser()
    config.read(conf)
    _sleep = int(config.get('Main', 'm3u8_sleep'))
    while True:
        now = int(time.time())
        last = int(cconfig.get('Loop', 'time'))
        if now > last + _sleep * 60 * 60:
            m3u8()
            cconfig.set('Loop', 'time', now)
            cconfig.write()
        else:
            Logger.info('m3u8 loop sleeping for %s sec...' % str(last + _sleep * 60 * 60 - now))
            time.sleep(int(last + _sleep * 60 * 60 - now))
    pass

if __name__ == "__main__":
    loop_m3u8()
