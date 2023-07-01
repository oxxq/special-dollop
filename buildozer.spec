[app]
title = Vavoo - LiveTV Parser
package.name = vavoo.parser
package.domain = org.mastaaa
source.dir = .
source.include_exts = py, db, json, png, kv
version = 1.3.2
requirements = python3, flask, kivy, kivymd, certifi>=2018.4.16, pillow, sqlite3, jnius, requests, urllib3, charset-normalizer==3.0.1, idna==3.4, chardet, pytz, oscpy
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE
orientation = portrait, landscape
fullscreen = 0
services = Task:services.py:foreground:sticky
#          archs = armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = armeabi-v7a, arm64-v8a, x86, x86_64
android.allow_backup = True
presplash.filename = %(source.dir)s/data/presplash.png
icon.filename = %(source.dir)s/data/icon.png
#p4a.bootstrap = sdl2
#p4a.branch = master
#android.accept_sdk_license = True

[buildozer]
log_level = 1
warn_on_root = 0

