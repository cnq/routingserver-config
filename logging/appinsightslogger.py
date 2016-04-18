import os
import shutil
import json
import applicationinsights
import re

logentryregex = re.compile('(?P<datetime>\d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d) \[(?P<level>[a-z]*)\] \d+#\d+: (\*(?P<connection>\d+) )?(?P<message>.*)', re.IGNORECASE)
xstr = lambda s: s or ""

def pushlogs(logdirectory, instrumentationkey):
	print 'log directory: ' +  logdirectory + ' instrumentationkey: ' + instrumentationkey
	stagingdirectory = logdirectory + '/appinsightslogstaging'

	print 'move log files to a staging location, staging location will be created if does not exists'
	files = os.listdir(logdirectory)
	#create staging location if it does not exists
	if not os.path.exists(stagingdirectory):
		print 'staging directory ' + stagingdirectory + ' does not exist.  creating...'
		os.makedirs(stagingdirectory)
	for file in files:
		srcfile = os.path.join(logdirectory, file)
		if os.path.isfile(srcfile):
			dstfile = os.path.join(stagingdirectory, file)
			shutil.copy2(srcfile, dstfile)
			os.remove(srcfile)
		
	print 'issuing reload logs command to nginx'
	os.system("sudo kill -USR1 `cat /var/run/nginx.pid`")

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
				processaccesslog(stagedfilepath, accountname, appname, instrumentationkey)
				os.remove(stagedfilepath)
			elif logtype == 'error':
				processerrorlog(stagedfilepath, accountname, appname, instrumentationkey)
				os.remove(stagedfilepath)
			else:
				print 'unknow file type: ' + stagedfile
		elif len(nametokens) == 2:
			processlog(stagedfilepath, instrumentationkey)
			os.remove(stagedfilepath)
		else:
			print 'unknow file type: ' + stagedfile

def processaccesslog(path, account, app, instrumentationkey):
	print 'processing access log: ' + path
	tc = applicationinsights.TelemetryClient(instrumentationkey)
	with open(path) as file:
		for line in file:
			logevent = json.loads(line)
			success = True
			if int(logevent['status']) >= 400:
					success = False
			url = logevent['scheme'] + '://' + logevent['host'] + logevent['request_uri']
			duration = int(float(logevent['request_time']) * 1000)
			tc.track_request( \
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

def processerrorlog(path, account, app, instrumentationkey):
	print 'processing error log: ' + path
	tc = applicationinsights.TelemetryClient(instrumentationkey)
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

def processlog(path, instrumentationkey):
	print 'processing log: ' + path
	tc = applicationinsights.TelemetryClient(instrumentationkey)
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

    logdirectory = "/var/log/nginx/"
    instrumentationkey = ""

    with open('/opt/conf/logging/instrumentationkey.txt', 'r') as myfile:
        instrumentationkey=myfile.read().replace('\n', '')

    pushlogs(logdirectory, instrumentationkey)

if __name__ == "__main__":
    main()

