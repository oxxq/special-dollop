import re, requests, json, urllib, base64, codecs, threading, random, gzip, ssl, sys, os, signal, time, sqlite3
import socket
from datetime import date, datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return '127.0.0.1'
