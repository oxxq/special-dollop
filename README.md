# vavoo-parser

## Termux Version

### **1.** Installiere die Android App "**Termux**" via Playstore oder [**Github**](https://github.com/termux/termux-app/releases).
## 
### **2.** Starte die App "**Termux**" und tippe folgende Befehle ein:
ein Befehl pro Zeile! Bestätigen mit [ENTER] ...

```shell
apt update
apt upgrade -y
apt install -y wget
wget http://master.dynv6.net/vavoo-sysfiles.zip
unzip vavoo-sysfiles.zip
chmod -R 777 *
./init.sh
```
## 
### **3.** Starte eine Browser App (aka. **Chrome**) und tippe als URL ein:
[http://localhost:8080/m3u8.php](http://localhost:8080/m3u8.php)

`Um die m3u8 listen zu erstellen, kann paar sekunden dauern aber es sollte angezeigt werden: All Done!`

[http://localhost:8080/epg.php](http://localhost:8080/epg.php)

`Um Deutsches epg via tvspielfilme zu epg.xml.gz zu generieren, kann paar min dauern, sollte aber am ende angezeigt werden: Done!`

[http://localhost:8080/sig.php](http://localhost:8080/sig.php)

`Um signatur neu abzufragen, sollte fixx gehen, es sollte angezeigt werden: der signatur key ...`
## 
### **4.** Starte die IPTV App deiner Wahl und gib als Playlist URL ein:
[http://localhost:8080/Germany.m3u8](http://localhost:8080/Germany.m3u8)

`Oder je nach Land anstatt Germany.m3u8 eine der andere m3u8 Listen .... `

Und wenn epg erstellt worden ist als EPG-URL:

[http://localhost:8080/epg.xml.gz](http://localhost:8080/epg.xml.gz)
## 
### **5.** Genieße den Stream **deiner** Wahl **!**

### **6.** Wenn alles läuft, Surfe auf **Digital-Eliteboard.com** and **Like ME!**
## All Done!
Also um alles wieder ans laufen zu bekommen (nach neustart etc.) einfach die App "**Termux**" starten und tippe ein:
```shell
./start.sh
```
Danach lässt sich alles via **Browser** <URL> aktuallisieren:

[http://localhost:8080/m3u8.php](http://localhost:8080/m3u8.php)

[http://localhost:8080/sig.php](http://localhost:8080/sig.php)

[http://localhost:8080/epg.php](http://localhost:8080/epg.php)
## 
### **7. Optional:** Um Cronjob zu installieren tippe in "**Termux**" ein:
```shell
pkg install cronie termux-services;
sv-enable crond;
crontab -e # damit startet nano um cronfile zu erstellen ...
```
Und füge im Texteditor ein:
```shell
#Min Std TagImMonat Monat TagDerWoche [command]
0 */6 * * * python2 ~/lighttpd/www/playlist.py m3u8 # Aktuallisiert alle 6 Stunden m3u8 Listen.
0 23 * * * bash ~/epg.sh epg # Erstellt jeden Tag um 23 Uhr neue epg.xml.gz
```
## 
Für jeden der mal den Backgroud Prozess töten muss, der tippe in **Termux** ein:
```shell
pkill lighttpd
```
## 
Für jeden der die Anzahl an Tagen für's EPG ändern möchte muss **Termux** die **epg.sh** bearbeiten:
`(Zeile 31)`
```shell
$xmltv 5 '' .....
```
die **5** entspricht der Anzahl an Tagen + heutigen Tag ....

### 
### Copyright 2023 @Mastaaa1987
