#!/data/data/com.termux/files/usr/bin/python2

import sys, re, os, requests, sqlite3, json, time, urllib, base64, codecs, threading, random, gzip, ssl
from datetime import date
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib2 import urlopen, Request, HTTPError

base_path = '/data/data/com.termux/files/home/lighttpd/www/'
json_file = os.path.join(base_path, 'data.json')
db = os.path.join(base_path, 'playlist.db')
hurl = 'http://localhost:8080'

def m3u8():
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
        if os.path.exists(os.path.join(base_path, '%s.m3u8' % group)):
            os.remove(os.path.join(base_path, '%s.m3u8' % group))
        tf = open(os.path.join(base_path, '%s.m3u8' % group), "w")
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
            tf = open(os.path.join(base_path, '%s.m3u8' % c['group']), "a")
            if not str(row[3]) == '' and not str(row[4]) == '':
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s" tvg-logo="%s" tvg-id="%s",%s' % (row[1], row[2], row[3], row[4], row[6]))
            elif not str(row[3]) == '' and str(row[4]) == '':
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s" tvg-logo="%s",%s' % (row[1], row[2], row[3], row[6]))
            elif not str(row[4]) == '' and  str(row[3]) == '':
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s" tvg-id="%s",%s' % (row[1], row[2], row[4], row[6]))
            else:
                tf.write('\n#EXTINF:-1 tvg-name="%s" group-title="%s",%s' % (row[1], row[2], row[6]))
            tf.write('\n#EXTVLCOPT:http-user-agent=VAVOO/2.6')
            tf.write('\n%s/playlist2.php?id=%s' % (hurl, row[0]))
            tf.close()
        else:
            print('error!')
    con.close()
    print('\nAll Done!')


def sig():
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


def sig2():
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
            print(sig)
    except Exception  as e:
        raise


def test():
    print('Python2 Test')


def main():
    if len(sys.argv) == 1:
        print('Play with the Best...')
    else:
        if sys.argv[1] == 'm3u8':
            m3u8()
        elif sys.argv[1] == 'sig':
            sig()
        elif sys.argv[1] == 'sig2':
            sig2()
        elif sys.argv[1] == 'test':
            test()
        else:
            print('Syntax Error!')


if __name__ == '__main__':
    main()

