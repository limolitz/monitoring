import sqlite3 as sql
import datetime
import sys
import json
# based on https://stackoverflow.com/questions/15884363/in-mozilla-firefox-how-do-i-extract-the-number-of-currently-opened-tabs-to-save

def getOpenedFirefoxTabs(sessionfile):
    j = json.loads(open(sessionfile, 'rb').read().decode('utf-8'))
    all_tabs = list(map(tabs_from_windows, j['windows']))
    return sum(map(len, all_tabs))

def info_for_tab(tab):
    try:
        return (tab['entries'][0]['url'], tab['entries'][0]['title'])
    except IndexError:
        return None
    except KeyError:
        return None
def tabs_from_windows(window):
    return list(map(info_for_tab, window['tabs']))

def getPathToDB():
  return '/home/florin/bin/QuantifiedSelf/Firefox/firefoxProcesses.db'

def saveToDatabase():
        con = None
        try:
                con = sql.connect(getPathToDB())
                cur = con.cursor()
                cur.execute("INSERT OR REPLACE INTO firefox VALUES (?,?,?)", (datetime.datetime.now().strftime("%s"), 'standard', getOpenedFirefoxTabs('/home/florin/.mozilla/firefox/3wxc4x2q.default/sessionstore.js')))
                con.commit()
                #cur.execute("INSERT OR REPLACE INTO firefox VALUES (?,?,?)", (datetime.datetime.now().strftime("%s"), 'nova', getOpenedFirefoxTabs('/home/florin/Dropbox/Programme/Firefox/jys16p25.Nova-sync/sessionstore.js')))
                #con.commit()

        except sql.Error, e:
                print "Error %s:" % e.args[0]
                sys.exit(1)

        finally:
                if con:
                        con.close()

if __name__ == '__main__':
        saveToDatabase()