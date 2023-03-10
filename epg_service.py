import re, json, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
from kivy.config import ConfigParser
from tvsp2xmltv import defaults
from tvsp2xmltv import tvsGrabber
from kivy.logger import Logger, LOG_LEVELS

Logger.setLevel(LOG_LEVELS["info"])

def epg():
    Logger.info('starting epg process ...')
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_rootdir, 'files')
    conf = os.path.join(_rootdir, 'main.ini')
    config = ConfigParser()
    config.read(conf)
    epg_grab = int(config.get('Main', 'epg_grab'))
    epg_channels = [ "123.tv", "13th Street Universal", "3sat", "Animal Planet", "ANIXE", "ARD alpha", "ARTE", "Auto Motor Sport", "AXN", "Bibel TV", "Bloomberg Europe TV", "BR", "Cartoon Network", "Classica", "Comedy Central", "CRIME + INVESTIGATION", "Das Erste", "DAZN", "DELUXE MUSIC", "Deutsches Musik Fernsehen", "Discovery HD", "Disney Channel", "DMAX", "Eurosport 1", "Eurosport 2", "Fix &amp; Foxi", "Health TV", "Heimatkanal", "History HD", "HR", "HSE24", "Jukebox", "kabel eins", "kabel eins classics", "kabel eins Doku", "KiKA", "KinoweltTV", "K-TV", "MDR", "Motorvision TV", "MTV", "N24 Doku", "Nat Geo HD", "NAT GEO WILD", "NDR", "nick", "Nick Jr.", "Nicktoons", "NITRO", "n-tv", "ONE", "ORF 1", "ORF 2", "ORF III", "ORF SPORT +", "PHOENIX", "ProSieben", "ProSieben Fun", "ProSieben MAXX", "Romance TV", "RTL", "RTL Crime", "RTL II", "RTL Living", "RTL Passion", "RTLplus", "SAT.1", "SAT.1 emotions", "SAT.1 Gold", "ServusTV", "Silverline", "sixx", "Sky Action", "Sky Atlantic HD", "Sky Cinema Best Of", "Sky Cinema Classics", "Sky Cinema Fun", "Sky Cinema Premieren", "Sky Cinema Premieren +24", "Sky Cinema Special HD", "Sky Cinema Thriller", "Sky Comedy", "Sky Crime", "Sky Family", "Sky Krimi", "Sky One", "Sony Channel", "Spiegel Geschichte", "Spiegel TV Wissen", "SUPER RTL", "SWR/SR", "Syfy", "tagesschau24", "Tele 5", "TLC", "TNT Comedy", "TNT Film", "TNT Serie", "TOGGO plus", "Universal Channel HD", "VOX", "VOXup", "WDR", "ZDF", "ZDFinfo", "ZDFneo" ]
    
    defaults.destination_file = os.path.join(_path, 'epg.xml')
    if os.path.exists(defaults.destination_file):
        os.remove(defaults.destination_file)
    grabber = tvsGrabber.TvsGrabber()
    grabber.grab_days = int(epg_grab)
    grabber.pictures = False
    for chan in epg_channels:
        grabber.add_channel(str(chan))
    Logger.info('start grabbing ...')
    grabber.start_grab()
    Logger.info('safe xml ...')
    grabber.save()
    
    Logger.info('epg process Done!')

def loop_epg():
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    cconf = os.path.join(_rootdir, 'epg_service.ini')
    cconfig = ConfigParser()
    cconfig.read(cconf)
    if not os.path.exists(cconf):
        cconfig.setdefaults('Loop', {'time': 0})
        cconfig.write()
    conf = os.path.join(_rootdir, 'main.ini')
    config = ConfigParser()
    config.read(conf)
    _sleep = int(config.get('Main', 'epg_sleep'))
    while True:
        now = int(time.time())
        last = int(cconfig.get('Loop', 'time'))
        if now > last + _sleep * 24 * 60 * 60:
            epg()
            cconfig.set('Loop', 'time', now)
            cconfig.write()
        else:
            Logger.info('epg loop sleeping for %s sec...' % str(last + _sleep * 24 * 60 * 60 - now))
            time.sleep(int(last + _sleep * 24 * 60 * 60 - now))
    pass

if __name__ == "__main__":
    loop_epg()
