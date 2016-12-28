SLYCE SRP CONTRIBUTION REPORTS
==============================

This app watches an eve wallet API and reports the top contributors
in the past week, month, and all time.  It also displays a progress
bar and goal based on the wallet balance.

Installation
------------

Install the python distribution files on your server, preferably
outside of anything visible by the webserver.

Create a directory that will be served by your webserver.  Copy
the wallet.html and wallet-config.json to that directory.  It
shouldn't matter if people can see your API key, use a read only
key with access to the wallet transactions and balance.

Setup a cron job to execute the script and place the output
into the web visible directory.

```
56 23 * * * cd /var/www/html/SOMEWHERE; /home/ME/STUFF/wallet.py
```


Configuration
-------------

Copy the wallet-config.json-dist to wallet-config.json and edit the
contents.  Replace the keyID and vCode with the values from your EVE API
key.   The type should be either "char" if this is a character account or
"corp" if this is a corporation API key.

```
{
        "type": "one word - corp or char",
        "keyID": "YOUR_KEY_HERE",
        "vCode": "YOUR_CODE_HERE"
}
```

You can also customize the wallet.html page to suit your needs.
