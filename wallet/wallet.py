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
def load_json( filename ):
        try:
                file = open(filename, "r")
                data = json.loads(file.read())
                file.close
                return data
        except IOError:
                return dict()

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
        rows.append({'ownerID1': k, 'amount':"{:,}".format(v)})
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


# load api keys
config = load_json( 'wallet-config.json' )
if not config or not config['keyID'] or not config['vCode']:
	print 'Enter your EVE API key in wallet-config.json'
	sys.exit(-1)

jdict = dict()

jdict['balance'] =  balance()
 
#Download the Account Balance Data
apiURL = 'https://api.eveonline.com/corp/WalletJournal.xml.aspx?vCode=%s&keyID=%s&accountKey=%s' % (config['vCode'], config['keyID'], accountKey)
print apiURL
downloadedData = urllib.urlopen(apiURL)

#Parse the data into the headers and lines of data
XMLData = xml.dom.minidom.parse(downloadedData)
#headerNode = XMLData.getElementsByTagName("rowset")[0]
#columnHeaders = headerNode.attributes['columns'].value.split(',')
columnHeaders = [ "date", "ownerID1", "amount", "reason" ]

dataNodes = XMLData.getElementsByTagName("row")

today = datetime.datetime.utcnow().toordinal()
sunday = datetime.date.fromordinal( today - (today % 7) )
sunlast = datetime.date.fromordinal( today - (today % 7) - 7)
thismonth = datetime.date.fromordinal(today).replace(day=1)
lastmonth = (thismonth - datetime.timedelta(days=1)).replace(day=1)

jdict['donations'] = []
jdict['donors'] = {}
top = {}
topw = {}
topw1 = {}
topm = {}
topm1 = {}
for row, dataNode in enumerate(dataNodes):
    if ( dataNode.attributes["ownerName1"].value != "SLYCE Hull Incidents Investigation Team" ):
        date = datetime.datetime.strptime(dataNode.attributes["date"].value,'%Y-%m-%d %H:%M:%S').date()
        top[dataNode.attributes["ownerID1"].value] = top.get(dataNode.attributes["ownerID1"].value, 0) + long((float)(dataNode.attributes["amount"].value))
        if ( date > sunday ):
             topw[dataNode.attributes["ownerID1"].value] = topw.get(dataNode.attributes["ownerID1"].value, 0) + long((float)(dataNode.attributes["amount"].value))
        elif (date > sunlast ):
             topw1[dataNode.attributes["ownerID1"].value] = topw1.get(dataNode.attributes["ownerID1"].value, 0) + long((float)(dataNode.attributes["amount"].value))
        if ( date > thismonth ):
             topm[dataNode.attributes["ownerID1"].value] = topm.get(dataNode.attributes["ownerID1"].value, 0) + long((float)(dataNode.attributes["amount"].value))
        elif (date > lastmonth ):
             topm1[dataNode.attributes["ownerID1"].value] = topm1.get(dataNode.attributes["ownerID1"].value, 0) + long((float)(dataNode.attributes["amount"].value))
	jrow = dict()
	jdict['donors'][dataNode.attributes['ownerID1'].value] = { 'name': dataNode.attributes["ownerName1"].value, 'img': get_img_url(dataNode.attributes['ownerID1'].value, dataNode.attributes['owner1TypeID'].value) }
        for col, columnHeader in enumerate(columnHeaders):
            if ( "amount" == columnHeader ):
		jrow[columnHeader] = "{:,}".format(long((float)(dataNode.attributes[columnHeader].value)))
            else:
		jrow[columnHeader] = dataNode.attributes[columnHeader].value
	jdict['donations'].append(jrow)

json5("top", top, jdict);
json5("top_week", topw, jdict);
json5("top_last_week", topw1, jdict);
json5("top_month", topm, jdict);
json5("top_last_month", topm1, jdict);

save_json("top.json", jdict)
