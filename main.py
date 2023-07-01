# kivy modules first
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem, IRightBodyTouch, OneLineAvatarIconListItem
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.logger import Logger, LOG_LEVELS, LoggerHistory
from kivy.properties import ObjectProperty, StringProperty, DictProperty
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.settings import SettingsWithTabbedPanel
from kivy.config import ConfigParser

# common modules
import re, requests, json, urllib, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
from multiprocessing import Process, Queue

from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient

# mylibs
from lib import *

if platform == 'android':
    from jnius import autoclass
elif platform in ('linux', 'linux2', 'macos', 'win'):
    from runpy import run_path
    from threading import Thread        
else:
    raise NotImplementedError("service start not implemented on this platform")

def signal_handler(signal, frame):
    print(" CTRL + C detected, exiting ... ")
    Logger.info(" CTRL + C detected, exiting ... ")
    exit(0)

class Main(Screen):
    pass

class ContentNavigationDrawer(MDBoxLayout):
    nav_drawer = ObjectProperty()

sm = ScreenManager()
sm.add_widget(Main(name='main'))

class MainApp(MDApp):
    button_data = DictProperty()
    _rootdir = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(_rootdir, 'database.db')
    conf = os.path.join(_rootdir, 'main.ini')
    _path = os.path.join(_rootdir, 'files')
    config = ConfigParser()
    config.read(conf)
    Logger.setLevel(LOG_LEVELS["info"])
    if not os.path.exists(conf):
        config.setdefaults('Main', {'flask_host': '0.0.0.0', 'flask_port': 5000, 'ip_service': 1, 'm3u8_host': 'http://' + get_ip_address() + '', 'm3u8_service': 1, 'm3u8_sleep': 12, 'epg_grab': 7, 'epg_service': 1, 'epg_sleep': 5, 'osc_port': 0})
        config.setdefaults('Loop', {'sig': 0, 'm3u8': 0, 'epg': 0})
        config.write()
    host = str(config.get('Main', 'flask_host'))
    port = int(config.get('Main', 'flask_port'))
    hurl = str(config.get('Main', 'm3u8_host'))
    ip = 'http://' + get_ip_address()
    if not os.path.exists(_path):
        os.makedirs(_path)
    elif not hurl == ip and int(config.get('Main', 'ip_service')) > 0:
        for f in os.scandir(_path):
            if f.is_file() and 'm3u8' in f.name:
                i = open(os.path.join(_path, f.name))
                o = open(os.path.join(_path, f.name+'.new'), "w")
                for l in i:
                    o.write(re.sub(hurl, ip, l))
                i.close()
                o.close()
                os.remove(os.path.join(_path, f.name))
                os.rename(os.path.join(_path, f.name+'.new'), os.path.join(_path, f.name))
        config.set('Main', 'm3u8_host', ip)
        config.write()

    def start_aService(self, name):
        from android import mActivity
        context =  mActivity.getApplicationContext()
        service_name = str(context.getPackageName()) + '.Service' + name
        service = autoclass(service_name)
        service.start(mActivity,'')   # starts or re-initializes a service
        return service

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.primary_hue = "400"
        self.settings_cls = MySettingsWithTabbedPanel
        self.config = ConfigParser()
        self.config.read(self.conf)
        self.server = server = OSCThreadServer()
        server.listen('localhost', default=True)
        server.bind(b'/log', self.recieve_log)
        server.bind(b'/echo', self.recieve_echo)
        server.bind(b'/reg', self.register_service)
        self.service = None
        self.client = None
        self.config.set('Main', 'osc_port', int(server.getaddress()[1]))
        self.config.write()

        self.button_data = {
            'Start M3u8 List creation': [
                'file-video',
                'on_release', lambda x: self.start_m3u8()
            ],
            'Start EPG grabbing': [
                'television-guide',
                'on_release', lambda x: self.start_epg()
            ],
            'Start Signatur-Key creation': [
                'refresh',
                'on_release', lambda x: self.start_sig()
            ],
            'Start All Services': [
                'play',
                'on_release', lambda x: self.start_service()
            ],
            'Stop All Services': [
                'stop',
                'on_release', lambda x: self.stop_service()
            ],
            'Settings': [
                'cog',
                'on_release', lambda x: self.open_settings()
            ],
            'Exit': [
                'power-standby',
                'on_release', lambda x: self.exit()
            ],
        }
    
    def on_start(self):
        self.start_service()
    
    def on_stop(self):
        Logger.info('terminating ALL and exiting ...')
        if self.client:
            self.client.send_message(b'/kill', [])

    def build_config(self, config):
        config.setdefaults('Main', {'flask_host': '0.0.0.0', 'flask_port': 5000, 'm3u8_host': 'http://' + get_ip_address() + '', 'm3u8_service': 1, 'm3u8_sleep': 12, 'epg_grab': 7, 'epg_service': 1, 'epg_sleep': 5})

    def build_settings(self, settings):
        settings.add_json_panel('Main', self.config, 'config.json')

    def on_config_change(self, config, section, key, value):
        Logger.info("main.py: App.on_config_change: {0}, {1}, {2}, {3}".format(
            config, section, key, value))

        if section == "My Label":
            if key == 'font_size':
                self.root.get_screen('main').ids.label.font_size = float(value)
            #elif key == "text":
                #self.root.get_screen('main').ids.label.text = value

    def close_settings(self, settings=None):
        Logger.info("main.py: App.close_settings: {0}".format(settings))
        super(MainApp, self).close_settings(settings)

    def register_service(self, message):
        msg = message.decode('utf8')
        self.client = OSCClient(b'localhost',int(msg))
        self.root.get_screen('main').ids.message.text += 'service tasks registered on port: %s\n' % str(msg)
    
    def recieve_echo(self, message):
        self.root.get_screen('main').ids.message.text += '{}\n'.format(message.decode('utf8'))
    
    def recieve_log(self, message):
        self.root.get_screen('main').ids.log.text += '{}\n'.format(message.decode('utf8'))

    def start_service(self):
        if platform == 'android':
            from android import mActivity
            context =  mActivity.getApplicationContext()
            SERVICE_NAME = str(context.getPackageName()) +\
                '.Service' + 'Task'
            self.service = autoclass(SERVICE_NAME)
            self.service.start(mActivity, '')

        elif platform in ('linux', 'linux2', 'macos', 'win'):
            # Usually 'import multiprocessing'
            # This is for debug of service.py behavior (not performance)
            self.service = Thread(
                target=run_path,
                args=['services.py'],
                kwargs={'run_name': '__main__'},
                daemon=True
            )
            self.service.start()
    
    def stop_service(self):
        if self.client:
            self.client.send_message(b'/kill', [])
    
    def start_epg(self):
        if self.client:
            self.client.send_message(b'/start_epg', [])

    def start_m3u8(self):
        if self.client:
            self.client.send_message(b'/start_m3u8', [])

    def start_sig(self):
        if self.client:
            self.client.send_message(b'/start_sig', [])

    def exit(self):
        Logger.info('terminating ALL and exiting ...')
        if self.client:
            self.client.send_message(b'/kill', [])
        sys.exit()

    def show_log(self):
        messages = [m.message for m in LoggerHistory.history]
        for m in messages:
            self.root.get_screen('main').ids.logs.add_widget(LogMessage(text=m))

class MySettingsWithTabbedPanel(SettingsWithTabbedPanel):
    def on_close(self):
        Logger.info('main.py: MySettingsWithTabbedPanel.on_close')

    def on_config_change(self, config, section, key, value):
        Logger.info("main.py: MySettingsWithTabbedPanel.on_config_change: ")
        Logger.info("{0}, {1}, {2}, {3}".format(config, section, key, value))


if __name__ == "__main__":
    #CTRL+C signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    MainApp().run()
