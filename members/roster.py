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
	json.dump(data, file)
	file.close

corp_cache = load_json( "corps.json" )
old = load_json( "chars.json" )
additions = load_json( "additions.json" )
subtractions = load_json( "subtractions.json" )
chars = dict()

def get_corp_info( id ):
	if id in corp_cache:
		return corp_cache[id]
	info = dict()
	try:
		apiURL = 'https://api.eveonline.com/corp/CorporationSheet.xml.aspx?corporationID=%s' % (id)
		print apiURL
		downloadedData = urllib2.urlopen(apiURL)
		root = ET.parse(downloadedData).getroot()
		info['ticker'] = root.find('.//ticker').text
		info['name'] = root.find('.//corporationName').text
		print 'TICKER: [%s] NAME [%s]' % (info['ticker'], info['name'])
		corp_cache[id] = info
	except:
		info = {'ticker': '???', 'name': '???'}
		pass
	return info

page=0
count=0

file = open("roster.csv", "w")
csvf = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
while True:
	url = "http://evewho.com/api.php?type=allilist&id=%s&page=%d" % (allianceId, page)
	print "URL %s" % (url)
	headers = { 'User-Agent' : 'Mozilla/5.0' }
	req = urllib2.Request(url, None, headers)
	data = urllib2.urlopen( req ).read()
	#print data
	output = json.loads(data)
	if not output["characters"]:
		break
	for c in output["characters"]:
		corp_info = get_corp_info( c['corporation_id'] )
		#file.write('%s,%s,%s' % (c['name'], corp_info['ticker'], corp_info['name']) )
		csvf.writerow([c['name'], corp_info['ticker'], corp_info['name']])
		chars[c['character_id']] = { 'name': c['name'], 'corp': c['corporation_id'] }
		count += 1
	time.sleep(1)
	page += 1

file.close

print "Read %d pages, Found %d characters" % (page, count)

for k, v in chars.iteritems():
	if not k in old:
		corp_info = get_corp_info( v['corp'] )
		additions[k] = { 'name': v['name'], 'corp': corp_info['name'], 'ticker': corp_info['ticker'], 'date': now }

for k, v in old.iteritems():
	if not k in chars:
		corp_info = get_corp_info( v['corp'] )
		subtractions[k] = { 'name': v['name'], 'corp': corp_info['name'], 'ticker': corp_info['ticker'], 'date': now }

save_json("chars.json", chars)
save_json("corps.json", corp_cache)
save_json("additions.json", additions)
save_json("subtractions.json", subtractions)

