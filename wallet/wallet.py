#!/usr/bin/env python
#
# Download wallet information from the EVE xml apis, extract top donors
#  * place Eve API key info in wallet-config.json
#
import urllib
import json
import sys
import xml.dom.minidom
import operator
import time
import datetime
import calendar

# Which corp wallet do we inspect, first is 1000
accountKey = '1000'

# load json from file, create empty dict if file doesn't exist or file error
def load_json( filename, new_json ):
	try:
		file = open(filename, "r")
		data = json.loads(file.read())
		file.close
		return data
	except IOError:
		return new_json

# save json to file
def save_json( filename, data ):
	file = open(filename, "w")
	json.dump(data, file)
	file.close

# Get the correct image path for the donor typeid: http://eve-files.com/chribba/typeid.txt
def get_img_url(id, typeid):
	if typeid == '2':
		return 'http://imageserver.eveonline.com/Corporation/%s_128.png' % ( id )
	elif typeid == '16159':
		return 'http://imageserver.eveonline.com/Alliance/%s_128.png' % ( id )
	# 1373-1386   Character + Race
	return 'https://imageserver.eveonline.com/Character/%s_128.jpg' % ( id )

# Extract the top 5 donors
def json5(label, donations, jdict):
	rows = []
	sorted_x = sorted(donations.items(), key=operator.itemgetter(1), reverse=True)
	for k,v in sorted_x:
		rows.append({'ownerID1': k, 'amount': v})
	jdict[label] = rows

# Download wallet balance
def balance():
	balanceApiURL = 'https://api.eveonline.com/corp/AccountBalance.xml.aspx?vCode=%s&keyID=%s&accountKey=%s' % (config['vCode'], config['keyID'], accountKey)
	downloadedData = urllib.urlopen(balanceApiURL)
	XMLData = xml.dom.minidom.parse(downloadedData)
	dataNodes = XMLData.getElementsByTagName("row")
	for row, dataNode in enumerate(dataNodes):
		if ( dataNode.attributes["accountKey"].value == "1000" ):
			return long((float)(dataNode.attributes["balance"].value))
	return 0

# Download wallet transactions, convert to json, de-dupe and merge with saved transaction history
def download_transactions(): 
	#Download the Account Balance Data
	apiURL = 'https://api.eveonline.com/corp/WalletJournal.xml.aspx?vCode=%s&keyID=%s&accountKey=%s' % (config['vCode'], config['keyID'], accountKey)
	print apiURL
	downloadedData = urllib.urlopen(apiURL)

	#Parse the data into the headers and lines of data
	XMLData = xml.dom.minidom.parse(downloadedData)
	headerNode = XMLData.getElementsByTagName("rowset")[0]
	columnHeaders = headerNode.attributes['columns'].value.split(',')
	# columnHeaders = [ "date", "ownerID1", "amount", "reason" ]
	int_columns = [ 'refID', 'refTypeID', 'ownerID1', 'ownerID2', 'argID1', 'owner1TypeID', 'owner2TypeID']
	float_columns = [ 'amount', 'balance', ]

	transactions = load_json( 'wallet-transactions.json', [] )

	tx_ids = []
	for trow in transactions:
		tx_ids.append(trow['refID'])

	dataNodes = XMLData.getElementsByTagName("row")
	for dataNode in dataNodes:
		if ( (long)(dataNode.attributes['refID'].value) in tx_ids):
			continue
		trow = dict()
		for col, columnHeader in enumerate(columnHeaders):
			if ( columnHeader in int_columns ):
				trow[columnHeader] = (long)(dataNode.attributes[columnHeader].value)
			elif ( columnHeader in float_columns ):
				trow[columnHeader] = (float)(dataNode.attributes[columnHeader].value)
			else:
				trow[columnHeader] = dataNode.attributes[columnHeader].value
		transactions.append(trow)

	save_json( 'wallet-transactions.json', transactions)

	return transactions

# load api keys
config = load_json( 'wallet-config.json', dict() )
if not config or not config['keyID'] or not config['vCode']:
	print 'Enter your EVE API key in wallet-config.json'
	sys.exit(-1)

transactions = download_transactions()

jdict = dict()
jdict['donations'] = []
jdict['donors'] = {}
jdict['balance'] =  balance()

report_fields = [ "date", "ownerID1", "amount", "reason" ]

today = datetime.datetime.utcnow().toordinal()
sunday = datetime.date.fromordinal( today - (today % 7) )
sunlast = datetime.date.fromordinal( today - (today % 7) - 7)
thismonth = datetime.date.fromordinal(today).replace(day=1)
lastmonth = (thismonth - datetime.timedelta(days=1)).replace(day=1)

top = {}
topw = {}
topw1 = {}
topm = {}
topm1 = {}
for r in transactions:
	if ( r["ownerName1"] == "SLYCE Hull Incidents Investigation Team" ):
		continue

	date = datetime.datetime.strptime(r["date"],'%Y-%m-%d %H:%M:%S').date()
	top[r["ownerID1"]] = top.get(r["ownerID1"], 0) + (float)(r["amount"])
	if ( date > sunday ):
		 topw[r["ownerID1"]] = topw.get(r["ownerID1"], 0) + (float)(r["amount"])
	elif (date > sunlast ):
		 topw1[r["ownerID1"]] = topw1.get(r["ownerID1"], 0) + (float)(r["amount"])
	if ( date > thismonth ):
		 topm[r["ownerID1"]] = topm.get(r["ownerID1"], 0) + (float)(r["amount"])
	elif (date > lastmonth ):
		 topm1[r["ownerID1"]] = topm1.get(r["ownerID1"], 0) + (float)(r["amount"])
	
	jrow = dict()
	jdict['donors'][r['ownerID1']] = { 'name': r["ownerName1"], 'img': get_img_url(r['ownerID1'], r['owner1TypeID']) }
	for f in report_fields:
		# if ( "amount" == f ):
		# 	jrow[f] = "{:,}".format(long((float)(r[f])))
		# else:
		jrow[f] = r[f]
	jdict['donations'].append(jrow)

json5("top", top, jdict);
json5("top_week", topw, jdict);
json5("top_last_week", topw1, jdict);
json5("top_month", topm, jdict);
json5("top_last_month", topm1, jdict);

save_json("top.json", jdict)

