#!/usr/bin/python

startTime='201804010000'

import json
import csv
import urllib2
import time
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET
import operator
import time
import datetime

now = datetime.datetime.utcnow().strftime('%Y-%m-%d');

def load_json( filename ):
	try:
		file = open(filename, "r")
		data = json.loads(file.read())
		file.close
		return data
	except IOError:
		return dict()

def save_json( filename, data ):
	file = open(filename, "w")
	json.dump(data, file, sort_keys=True, indent=2)
	file.close

kills = load_json( "kills.json" )
killers = load_json( "killers.json" )
alliances = load_json( "alliances.json" )

def refresh_alliances():
	url = 'https://api.eveonline.com/eve/AllianceList.xml.aspx?version=1'
	downloadedData = urllib2.urlopen(url)
	XMLData = xml.dom.minidom.parse(downloadedData)
	dataNodes = XMLData.getElementsByTagName("row")
	for row, dataNode in enumerate(dataNodes):
		a = dict()
		a['name'] = dataNode.attributes["name"].value
		a['ticker'] = dataNode.attributes["shortName"].value
		alliances[dataNode.attributes["allianceID"].value] = a
	return 0

refresh_alliances()

page=1
count=0

# Read latest killmails
while True:
	url = 'https://zkillboard.com/api/shipID/41030/startTime/%s/page/%d/' % (startTime, page)
	print "URL %s" % (url)
	headers = { 'User-Agent' : 'Mozilla/5.0' }
	req = urllib2.Request(url, None, headers)
	data = urllib2.urlopen( req ).read()
	output = json.loads(data)
	if not output:
		break
	for k in output:
		# corp_info = get_corp_info( c['corporation_id'] )
                # Use string key, file writer converts to string but string 1 & int 1 are seen as two keys until written            
		kills[str(k['killmail_id'])] = k
		count += 1
	time.sleep(1)
	page += 1

print "Read %d pages, Found %d kills, Total %d kills" % (page, count, len(kills))

for k in killers:
    killers[k]['kills'] = 0
    killers[k]['isk'] = 0

for k in kills:
    v = kills[k]
    if not 'alliance_id' in v['victim']:
        continue
    if v['zkb']['npc']:
        continue
    id = str(v['victim']['alliance_id'])
    if id in killers:
        killers[id]['kills'] += 1
        killers[id]['isk'] += v['zkb']['fittedValue']
    else:
        c = dict()
        c['id'] = id
        c['kills'] = 1
        c['isk'] = 0
        if id in alliances:
            c['name'] = alliances[id]['name']
            c['ticker'] = alliances[id]['ticker']
        killers[id] = c

save_json("kills.json", kills)
save_json("killers.json", killers)
save_json("alliances.json", alliances)
