import os
import shutil
import json
import re
import time

logentryregex = re.compile('(?P<datetime>\d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d) \[(?P<level>[a-z]*)\] \d+#\d+: (\*(?P<connection>\d+) )?(?P<message>.*)', re.IGNORECASE)
xstr = lambda s: s or ""
tc = None

def testlogs(logdirectory):
    
    stagingdirectory = logdirectory + '/appinsights'
    print 'testing log files in directory: ' + stagingdirectory
    
    if len(os.listdir(stagingdirectory)) > 0:
        print 'found ' + str(len(os.listdir(stagingdirectory))) + ' files to test'
        testfiles(stagingdirectory)
    else:
        print 'there are no log files to test.  exiting...'




def testfiles(stagingdirectory):
    stagedfiles = os.listdir(stagingdirectory)
    for stagedfile in stagedfiles:
        print 'testing: ' + stagedfile
        stagedfilepath = os.path.join(stagingdirectory, stagedfile)
        nametokens = stagedfile.split('.')
        if len(nametokens) == 4:
            accountname = nametokens[0]
            appname = nametokens[1]
            logtype = nametokens[2]
            print 'accountname: ' + accountname
            print 'appname: ' + appname
            if logtype == 'access':
            	testaccesslog(stagedfilepath, accountname, appname)
            elif logtype == 'error':
            	testerrorlog(stagedfilepath, accountname, appname)
            else:
            	print 'this file would not be processed during normal processing.  unknow file type: ' + stagedfile
        elif len(nametokens) == 2:
            testlog(stagedfilepath)
        else:
            print 'this file would not be processed during normal processing.  unknow file type: ' + stagedfile

def testaccesslog(path, account, app):
	print 'testing access log: ' + path
	with open(path) as file:
		for line in file:
			logevent = None
			try:
					logevent = json.loads(line)
			except:
					print 'BAD ACCESSLOG ENTRY.  Unable to load to json object - ' + line
					continue
			try:
				success = True
				if int(logevent['server_level']) == 1 and logevent['cache_status_regular'] != "HIT":
						continue
				if int(logevent['status']) >= 400:
						success = False
				request_url = logevent['request_scheme'] + '://' + logevent['request_host_header'] + logevent['request_uri']
				duration = int(float(logevent['request_time']) * 1000)
			except:
					print 'BAD ACCESSLOG ENTRY.  Unexpected values - ' + line
					continue
	print 'finished processing access log: ' + path		


def testerrorlog(path, account, app):
	print 'testing error log: ' + path
	with open(path) as file:
		for line in file:
			match = logentryregex.match(line)
	print 'finished testing error log: ' + path

def testlog(path):
	print 'testing log: ' + path
	with open(path) as file:
		for line in file:
			match = logentryregex.match(line)
	print 'finished testing log: ' + path


def main(args=None):

    logdirectory = "/var/log"
    testlogs(logdirectory)


if __name__ == "__main__":
    main()

