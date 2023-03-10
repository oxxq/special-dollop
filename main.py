# kivy modules first
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem, IRightBodyTouch, OneLineAvatarIconListItem
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.logger import Logger, LOG_LEVELS
from kivy.properties import ObjectProperty
from kivy.logger import LoggerHistory
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.lang.builder import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.settings import SettingsWithTabbedPanel
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.properties import DictProperty
from kivy.config import ConfigParser

# common modules
import re, requests, json, urllib, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
from socket import getaddrinfo, gethostname
import ipaddress
from datetime import date, datetime
import certifi as cfi
from threading import Thread
from multiprocessing import Process, Queue
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Flask modules
from flask import Flask, request, render_template, make_response, redirect, abort, send_from_directory

# mylibs
from lib import *
from flask_service import *
from m3u8_service import *
from sig_service import *
from epg_service import *

if platform == 'android':
    from jnius import autoclass
    from android import mActivity

def signal_handler(signal, frame):
    print(" CTRL + C detected, exiting ... ")
    Logger.info(" CTRL + C detected, exiting ... ")
    exit(0)

Main_overlay = '''
<ContentNavigationDrawer>:
    orientation: "vertical"
    padding: "8dp"
    spacing: "8dp"

    AnchorLayout:
        anchor_x: "left"
        size_hint_y: None
        height: avatar.height

        Image:
            id: avatar
            size_hint: None, None
            size: "56dp", "56dp"
            source: "data/icon.png"

    MDLabel:
        text: "Mastaaa's Vavoo-Parser"
        font_style: "Button"
        size_hint_y: None
        height: self.texture_size[1]

    MDLabel:
        text: "sebastianspaaa@gmail.com"
        font_style: "Caption"
        size_hint_y: None
        height: self.texture_size[1]

    ScrollView:
        MDList:
            OneLineAvatarListItem:
                text: "Start All Services"
                on_press: app.start_services()
                on_release: root.nav_drawer.set_state("close")
                IconLeftWidget:
                    icon: 'play'

            OneLineAvatarListItem:
                text: "Stop All Services"
                on_press: app.stop_services()
                on_release: root.nav_drawer.set_state("close")
                IconLeftWidget:
                    icon: 'stop'

            OneLineAvatarListItem:
                text: "Settings"
                on_press: app.open_settings()
                on_release: root.nav_drawer.set_state("close")
                IconLeftWidget:
                    icon: 'cog'

            OneLineAvatarListItem:
                text: "Exit"
                on_press: app.exit()
                on_release: root.nav_drawer.set_state("close")
                IconLeftWidget:
                    icon: 'power-standby'


ScreenManager:
    Main:
<Main>:
    name : 'main'
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: toolbar
            title: "Vavoo - LiveTV Parser"
            md_bg_color: app.theme_cls.primary_color
            left_action_items: [['menu', lambda x: nav_drawer.set_state("open")]]

        MDScrollView:
            id: label
            MDList:
                id: container

        MDFloatingActionButtonSpeedDial:
            data: app.button_data
            root_button_anim: True

    MDNavigationDrawer:
        id: nav_drawer
        radius: (0, 16, 16, 0)

        ContentNavigationDrawer:
            nav_drawer: nav_drawer
'''

class Main(Screen):
    pass

class ContentNavigationDrawer(MDBoxLayout):
    nav_drawer = ObjectProperty()

global p1, p2, p3, p4, p5, p6
p1 = None
p2 = None
p3 = None
p4 = None
p5 = None
p6 = None
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
        config.setdefaults('Main', {'flask_host': '0.0.0.0', 'flask_port': 5000, 'm3u8_host': 'http://' + get_ip_address() + '', 'm3u8_service': 1, 'm3u8_sleep': 12, 'epg_grab': 7, 'epg_service': 1, 'epg_sleep': 5})
        config.write()
    host = str(config.get('Main', 'flask_host'))
    port = int(config.get('Main', 'flask_port'))
    hurl = str(config.get('Main', 'm3u8_host'))
    if not os.path.exists(_path):
        os.makedirs(_path)

    if platform == 'android':
        def start_aService(self, name):
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
        self.root = Builder.load_string(Main_overlay)
        self.config = ConfigParser()
        self.config.read(self.conf)

        self.button_data = {
            'Start M3u8 List Creation': [
                'play',
                'on_release', lambda x: self.start_m3u8()
            ],
            'Start EPG xml.gz Creation': [
                'stop',
                'on_release', lambda x: self.start_epg()
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

        return self.root
    
    def on_start(self):
        self.start_services()
    
    def on_stop(self):
        Logger.info('terminating ALL and exiting ...')
        self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='terminating ALL and exiting ...'))
        self.stop_all()

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

    def exit(self):
        Logger.info('terminating ALL and exiting ...')
        self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='terminating ALL and exiting ...'))
        self.stop_all()
        sys.exit()

    def start_m3u8(self):
        global p5
        if not p5:
            self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting m3u8 list creation ...'))
            p5 = Process(target=m3u8)
            p5.start()
        else:
            p5.join(timeout=0)
            if p5.is_alive():
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='m3u8 list creation allready in progress!'))
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting m3u8 list creation ...'))
                p5 = Process(target=m3u8)
                p5.start()

    def start_epg(self):
        global p6
        if not p6:
            self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting epg xml.gz creation ...'))
            p6 = Process(target=epg)
            p6.start()
        else:
            p6.join(timeout=0)
            if p6.is_alive():
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='epg xml.gz creation allready in progress!'))
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting epg xml.gz creation ...'))
                p6 = Process(target=epg)
                p6.start()

    def stop_services(self):
        self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='stopping All Process Services ...'))
        if platform == 'android':
            self.start_aService('Flask').stop(mActivity)
            ifp2 = bool(self.config.get('Main', 'm3u8_service'))
            if ifp2 == True:
                self.start_aService('M3u8').stop(mActivity)
            self.start_aService('Signatur').stop(mActivity)

            ifp4 = bool(self.config.get('Main', 'epg_service'))
            if ifp4 == True:
                self.start_aService('Epg').stop(mActivity)
        else:
            global p1, p2, p3, p4
            if p1:
                p1.join(timeout=0)
                if p1.is_alive():
                    Logger.info('killing p1 ...')
                    p1.terminate()
                    p1 = None
            if p2:
                p2.join(timeout=0)
                if p2.is_alive():
                    Logger.info('killing p2 ...')
                    p2.terminate()
                    p2 = None
            if p3:
                p3.join(timeout=0)
                if p3.is_alive():
                    Logger.info('killing p3 ...')
                    p3.terminate()
                    p3 = None
            if p4:
                p4.join(timeout=0)
                if p4.is_alive():
                    Logger.info('killing p4 ...')
                    p4.terminate()
                    p4 = None

    def stop_all(self):
        self.stop_services()
        global p5, p6
        if p5:
            p5.join(timeout=0)
            if p5.is_alive():
                Logger.info('killing p5 ...')
                p5.terminate()
                p5 = None
        if p6:
            p6.join(timeout=0)
            if p6.is_alive():
                Logger.info('killing p6 ...')
                p6.terminate()
                p6 = None

    def start_services(self):
        if platform == 'android':
            self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting Flask Server on IP: %s & Port: %s ...' %(str(self.host), str(self.port))))
            self.start_aService('Flask')
            ifp2 = bool(self.config.get('Main', 'm3u8_service'))
            if ifp2 == True:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting M3u8 Service ...'))
                self.start_aService('M3u8')
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='M3u8 Service are Disabled in Settings!'))
            self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting Signatur Service ...'))
            self.start_aService('Signatur')
            ifp4 = bool(self.config.get('Main', 'epg_service'))
            if ifp4 == True:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting EPG Grab Service ...'))
                self.start_aService('Epg')
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='EPG Grab Service are Disabled in Settings!'))
        else:
            global p1, p2, p3, p4
            if p1:
                p1.join(timeout=0)
                if not p1.is_alive():
                    self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting Flask Server on IP: %s & Port: %s ...' %(str(self.host), str(self.port))))
                    p1 = Process(target=start_flask)
                    p1.start()  #launch Flask as separate process
                else:
                    self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='Flask Service allready started!'))
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting Flask Server on IP: %s & Port: %s ...' %(str(self.host), str(self.port))))
                p1 = Process(target=start_flask)
                p1.start()  #launch Flask as separate process

            ifp2 = bool(self.config.get('Main', 'm3u8_service'))
            if ifp2 == True:
                if p2:
                    p2.join(timeout=0)
                    if not p2.is_alive():
                        self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting M3u8 Service ...'))
                        p2 = Process(target=loop_m3u8)
                        p2.start()  #launch Flask as separate process
                    else:
                        self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='M3u8 Service allready started!'))
                else:
                    self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting M3u8 Service ...'))
                    p2 = Process(target=loop_m3u8)
                    p2.start()  #launch Flask as separate process
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='M3u8 Service are Disabled in Settings!'))

            if p3:
                p3.join(timeout=0)
                if not p3.is_alive():
                    self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting Signatur Service ...'))
                    p3 = Process(target=loop_sig)
                    p3.start()  #launch Flask as separate process
                else:
                    self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='Signatur Service allready started!'))
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting Signatur Service ...'))
                p3 = Process(target=loop_sig)
                p3.start()  #launch Flask as separate process

            ifp4 = bool(self.config.get('Main', 'epg_service'))
            if ifp4 == True:
                if p4:
                    p4.join(timeout=0)
                    if not p4.is_alive():
                        self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting EPG Grab Service ...'))
                        p4 = Process(target=loop_epg)
                        p4.start()  #launch Flask as separate process
                    else:
                        self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='EPG Grab Service allready started!'))
                else:
                    self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='starting EPG Grab Service ...'))
                    p4 = Process(target=loop_epg)
                    p4.start()  #launch Flask as separate process
            else:
                self.root.get_screen('main').ids.container.add_widget(OneLineListItem(text='EPG Grab Service are Disabled in Settings!'))

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
