[app]
title = Vavoo - LiveTV Parser
package.name = vavoo.parser
package.domain = org.mastaaa
source.dir = .
source.include_exts = py, db, json, png
version = 1.0
requirements = python3, flask, kivy, kivymd, certifi>=2018.4.16, pillow, sqlite3, jnius, requests, urllib3, charset-normalizer==3.0.1, idna==3.4, chardet, pytz
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
orientation = portrait
fullscreen = 0
services = Flask:flask_service.py, M3u8:m3u8_service.py, Signatur:sig_service.py, Epg:epg_service.py
#android.archs = armeabi-v7a, arm64-v8a
android.archs = armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 1
warn_on_root = 0
presplash.filename = %(source.dir)/data/presplash.png
icon.filename = %(source.dir)/data/icon.png
