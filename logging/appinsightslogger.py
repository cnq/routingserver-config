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
	files = os.listdir(logdirectory)
	#create staging location if it does not exists
	if not os.path.exists(stagingdirectory):
		print 'staging directory ' + stagingdirectory + ' does not exist.  creating...'
		os.makedirs(stagingdirectory)


	os.system("sudo cp -l /var/log/nginx/* " + stagingdirectory + "; sudo rm -fr /var/log/nginx; sudo mkdir -m 777 /var/log/nginx; sudo kill -USR1 `cat /var/run/nginx.pid`; sleep 1")

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
		elif len(nametokens) == 2:
			processlog(stagedfilepath)
			os.remove(stagedfilepath)
		else:
			print 'unknow file type: ' + stagedfile

def processaccesslog(path, account, app):
	print 'processing access log: ' + path
	with open(path) as file:
		for line in file:
			logevent = json.loads(line)
			success = True
			if int(logevent['status']) >= 400:
					success = False
			url = logevent['scheme'] + '://' + logevent['host'] + logevent['request_uri']
			duration = int(float(logevent['request_time']) * 1000)
			tc.track_request(\
					url, \
					url, \
					success, \
					logevent['event_time'], \
					duration, \
					logevent['status'], \
					logevent['request_method'], \
					{ \
						'account': account, \
						'app': app, \
						'remoteaddress': logevent['remote_addr'], \
						'useragent': logevent['http_user_agent'], \
						'referrer': logevent['http_referrer'], \
						'bytes_sent_to_client': logevent['bytes_sent'], \
						'incoming_request_length': logevent['request_length'], \
						'connection_number': logevent['connection'], \
						'connection_request_count': logevent['connection_requests'], \
						'host': logevent['host'], \
						'query_string': logevent['query_string'], \
						'request': logevent['request'], \
						'server_name': logevent['server_name'], \
						'server_port': logevent['server_port'], \
						'scheme': logevent['scheme'], \
						'protocol': logevent['server_protocol'], \
						'request_country': logevent['geoip_country_code'], \
						'cache_status': logevent['upstream_cache_status'] \
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

    logdirectory = "/var/log/"
    instrumentationkey = ""

    with open('/opt/conf/logging/instrumentationkey.txt', 'r') as myfile:
        instrumentationkey = myfile.read().replace('\n', '')

    pushlogs(logdirectory, instrumentationkey)
    print("Sleep for 5 seconds")
    time.sleep(5)

if __name__ == "__main__":
    main()

