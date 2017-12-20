#!/usr/bin/python

# Get somewhat stale member data for an alliance (I'm not sure how often EveWho data is updated)
#  * https://forums.eveonline.com/default.aspx?g=posts&t=25940&p=2 - Characters are updated every
#    few days. Also, I might not have the missing character in the database. If you know who it
#    is search for their name and they'll get added automatically.
# 
# Generates a CSV with names and corp info for all current members of the alliance (according to EveWho)
#  * roster.csv
#
# Also generates json files:
#  * chars.json - current roster
#  * additions.json - chars added since last run of tool
#  * subtractions.json - chars left since last run of tool
#  * corps - corporation names & tickers

# Change to your alliance id
allianceId='1042504553'
startTime='201712010000'

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

# Get the correct image path for the donor typeid: http://eve-files.com/chribba/typeid.txt
def get_img_url(id, typeid, refTypeID):
	# Shitty data cleanup, if no owner type guess corp if was corp wallet transaction
	if typeid == 0:
		if refTypeID == 37:
			typeid = 2
	if typeid == 2:
		return 'http://imageserver.eveonline.com/Corporation/%s_128.png' % ( id )
	elif typeid == 16159:
		return 'http://imageserver.eveonline.com/Alliance/%s_128.png' % ( id )
	# 1373-1386   Character + Race
	return 'https://imageserver.eveonline.com/Character/%s_128.jpg' % ( id )

# Lookup character name
def get_char_name(id):
	apiURL = 'https://api.eveonline.com/eve/CharacterName.xml.aspx?ids=%s' % (id)
	print apiURL
	downloadedData = urllib2.urlopen(apiURL)
	XMLData = xml.dom.minidom.parse(downloadedData)
	name = XMLData.getElementsByTagName("row")[0].attributes['name'].value
	return name

chars = load_json( "chars.json" )
corp_cache = load_json( "corps.json" )
victims = load_json( "victims.json" )
kills = load_json( "kills.json" )

def get_corp_info( id ):
        id = str(id)
	if id in corp_cache:
		return corp_cache[id]
	info = dict()
	try:
		apiURL = 'https://api.eveonline.com/corp/CorporationSheet.xml.aspx?corporationID=%s' % (id)
		print apiURL
		downloadedData = urllib2.urlopen(apiURL)
		root = ET.parse(downloadedData).getroot()
		info['id'] = id
		info['ticker'] = root.find('.//ticker').text
		info['name'] = root.find('.//corporationName').text
		print 'TICKER: [%s] NAME [%s]' % (info['ticker'], info['name'])
                info['image'] = get_img_url(id,2,99)
		corp_cache[id] = info
	except:
		info = {'ticker': '???', 'name': '???', 'image': ''}
		pass
	return info

page=1
count=0

# Read latest killmails
while False:
	url = "https://zkillboard.com/api/allianceID/%s/reset/groupID/101/startTime/201712010000/page/%d/" % (allianceId, page)
	print "URL %s" % (url)
	headers = { 'User-Agent' : 'Mozilla/5.0' }
	req = urllib2.Request(url, None, headers)
	data = urllib2.urlopen( req ).read()
	#print data
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

for k,v in chars.iteritems():
    v['kills'] = 0

for k,v in kills.iteritems():
    if str(v['victim']['alliance_id']) == allianceId:
        continue
    for a in v['attackers']:
        print a
        if not 'character_id' in a:
            continue
        if not 'alliance_id' in a:
            continue
        if str(a['alliance_id']) != allianceId:
            continue
        id = str(a['character_id'])
        if id in chars:
            chars[id]['kills'] += 1
        else:
            c = dict()
            c['id'] = id
            if 'corporation_id' in a:
                c['corp'] = get_corp_info(a['corporation_id'])
            c['name'] = get_char_name(id)
            c['image'] = get_img_url(id,99,99)
            c['kills'] = 1
            chars[id] = c

for k,v in victims.iteritems():
    v['kills'] = 0
    v['losses'] = 0

for k,val in kills.iteritems():
    v = val['victim']
    zkb = val['zkb']
    if str(v['alliance_id']) == allianceId:
        continue
    id = str(v['alliance_id'])
    if id in victims:
        victims[id]['kills'] += 1
        victims[id]['losses'] += zkb['fittedValue']
    else:
        c = dict()
        c['id'] = id
        c['kills'] = 1
        c['losses'] = zkb['fittedValue']
        victims[id] = c

save_json("kills.json", kills)
save_json("chars.json", chars)
save_json("corps.json", corp_cache)
save_json("victims.json", victims)

