SLYCE MEMBER TRACKER
====================

Tracks the characters entering and leaving the alliance as a
double check on member tracking.   Each day we scrape the member
list from evewho and compare it to the previous day.

Installation
------------

Install the python distribution files on your server, preferably
outside of anything visible by the webserver.

Create a directory that will be served by your webserver.  Copy
the roster.html to that directory.

I setup a cron job to execute the script and place the output
into the web visible directory.

```
52 23 * * * cd /var/www/html/SOMEWHERE; /home/ME/STUFF/roster.py
```

Configuration
-------------

Enter your alliance ID from evewho or eve near to top of roster.py

```
# Change to your alliance id
allianceId='1042504553'
```

Update the html and styles in roster.html as appropriate for your alliance.

Edit the paths in the ajax calls near the bottom of roster.html.  Replace
the /slyce/info path with the prefix to the generated json files as seen
externally on your webserver.

```
$.getJSON( "/slyce/info/subtractions.json" )
```
