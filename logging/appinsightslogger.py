import os
import shutil
import json
import applicationinsights
import re
import time

logentryregex = re.compile('(?P<datetime>\d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d) \[(?P<level>[a-z]*)\] \d+#\d+: (\*(?P<connection>\d+) )?(?P<message>.*)', re.IGNORECASE)
xstr = lambda s: s or ""
tc = None

def pushlogs(logdirectory, instrumentationkey):
    print 'log directory: ' + logdirectory + ' instrumentationkey: ' + instrumentationkey
    
    
    global tc
    if tc is None:
        tc = applicationinsights.TelemetryClient(instrumentationkey)
    
    tc.track_event("Logging")
    
    stagingdirectory = logdirectory + '/appinsights'
    
    print 'move log files to a staging location, staging location will be created if does not exists'
    os.system("sudo mkdir -p -m 777 " + stagingdirectory)
    
    if len(os.listdir(stagingdirectory)) > 0:
        print 'the staging directory ' + stagingdirectory + ' has files that have not yet been processed.  processing these before moving in new files'
        processfiles(stagingdirectory)
    else:
        print 'copying from nginx log location'
        os.system("sudo cp -l /var/log/nginx/* " + stagingdirectory + "; sudo rm -fr /var/log/nginx; sudo mkdir -m 777 /var/log/nginx; sudo kill -USR1 `cat /var/run/nginx.pid`; sleep 1")
        processfiles(stagingdirectory)




def processfiles(stagingdirectory):
    stagedfiles = os.listdir(stagingdirectory)
    for stagedfile in stagedfiles:
        print 'processing ' + stagedfile
        stagedfilepath = os.path.join(stagingdirectory, stagedfile)
        nametokens = stagedfile.split('.')
        if len(nametokens) == 4:
            accountname = nametokens[0]
            appname = nametokens[1]
            logtype = nametokens[2]
            print 'accountname: ' + accountname
            print 'appname: ' + appname
            if logtype == 'access':
            	processaccesslog(stagedfilepath, accountname, appname)
            	os.remove(stagedfilepath)
            elif logtype == 'error':
            	processerrorlog(stagedfilepath, accountname, appname)
            	os.remove(stagedfilepath)
            else:
                print 'unknow file type: ' + stagedfile
                os.remove(stagedfilepath)
        elif len(nametokens) == 2:
            processlog(stagedfilepath)
            os.remove(stagedfilepath)
        else:
            print 'unknow file type: ' + stagedfile
            os.remove(stagedfilepath)

def processaccesslog(path, account, app):
	print 'processing access log: ' + path
	with open(path) as file:
		for line in file:
			logevent = json.loads(line)
			success = True
			if int(logevent['server_level']) == 1 and logevent['cache_status_regular'] != "HIT":
					continue
			if int(logevent['status']) >= 400:
					success = False
			request_url = logevent['request_scheme'] + '://' + logevent['request_host_header'] + logevent['request_uri']
			duration = int(float(logevent['request_time']) * 1000)
			tc.track_request(\
					request_url, \
					request_url, \
					success, \
					logevent['event_time'], \
					duration, \
					logevent['status'], \
					logevent['request_method'], \
					{ \
						'account': account, \
						'app': app, \
						'request': logevent['request'], \
						'request_query_string': logevent['request_query_string'], \
						'request_method': logevent['request_method'], \
						'request_length': logevent['request_length'], \
						'request_referrer': logevent['request_referrer'], \
						'request_user_agent': logevent['request_user_agent'], \
						'request_mainstream_user_agent': logevent['request_mainstream_user_agent'], \
						'requestor_ipaddress': logevent['requestor_ipaddress'], \
						'requestor_country': logevent['requestor_country'], \
						'requestor_user': logevent['requestor_user'], \
						'connection_id': logevent['connection_id'], \
						'connection_request_count': logevent['connection_request_count'], \
						'server_level': logevent['server_level'], \
						'cache_status_regular': logevent['cache_status_regular'], \
						'cache_status_bot': logevent['cache_status_bot'], \
						'route_used': logevent['route_used'], \
						'backend_target': logevent['backend_target'], \
						'backend_request_url': logevent['backend_request_url'], \
						'backend_user_agent_sent': logevent['backend_user_agent_sent'], \
						'bytes_sent': logevent['bytes_sent'], \
						'status': logevent['status'] \
					})
	tc.flush()

def processerrorlog(path, account, app):
	print 'processing error log: ' + path
	with open(path) as file:
		for line in file:
			match = logentryregex.match(line)
			if match:
				tc.track_trace(match.group('level') + ' - ' + match.group('message'), \
				   { \
				   		'account': account, \
						'app': app, \
						'level': xstr(match.group('level')), \
						'logtime': xstr(match.group('datetime')), \
						'connection_number': xstr(match.group('connection')) \
					})
			else:
				tc.track_trace(line)
	tc.flush()

def processlog(path):
	print 'processing log: ' + path
	with open(path) as file:
		for line in file:
			match = logentryregex.match(line)
			if match:
				tc.track_trace(match.group('level') + ' - ' + match.group('message'), \
				   { \
						'level': xstr(match.group('level')), \
						'logtime':xstr(match.group('datetime')), \
						'connection_number': xstr(match.group('connection')) \
					})
			else:
				tc.track_trace(line)
	tc.flush()

	


def main(args=None):

    print("Starting application insights logging process.")
    print("Sleep for 5 seconds")
    time.sleep(5)

    logdirectory = "/var/log"
    instrumentationkey = ""

    with open('/opt/conf/logging/instrumentationkey.txt', 'r') as myfile:
        instrumentationkey = myfile.read().replace('\n', '')

    pushlogs(logdirectory, instrumentationkey)


if __name__ == "__main__":
    main()

