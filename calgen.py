#!/usr/bin/env python3

from DecryptionExample import DocumentKey
import xmltodict
import os.path
import datetime
from dateutil import parser
import ics
import pickle
import configparser
from webdav3.client import Client
import zipfile
from collections import OrderedDict

from pprint import pprint

should_log = True
def log(message):
	if should_log:
		print(message)

def add_basepath(path=''):
	if config.has_section('WEBDAV') and 'basepath' in config['WEBDAV'] and config['WEBDAV']['basepath'] is not None:
		basepath = config['WEBDAV']['basepath']
		return '{}/{}'.format(basepath, path)
	else:
		return '/{}'.format(path)

def datealize(timestr):
	timestr = parser.isoparse(timestr)
	if timestr.tzname() is None:
		timestr = timestr.astimezone(datetime.timezone.utc)
	return timestr

def get_alarms(task):
	# search for alarms that match the task
	task_id = task['@id']
	alarms_found = [alarm for alarm in contents['omnifocus']['alarm'] if alarm['task']['@idref'] == task_id]
	# extract information based on which alarm type it is
	alarms = []
	for alarm in alarms_found:
		trig = None
		if alarm['kind'] == 'due-relative':
			# datetime.timedelta #kind: due-relative -> fire-offset
			trig = datetime.timedelta(seconds = int(alarm['fire-offset']))
		elif alarm['kind'] == 'absolute':
			# datetime.datetime #kind: absolute -> fire-date
			trig = datealize(alarm['fire-date'])
		if trig is not None:
			alarms.append(ics.DisplayAlarm(trigger=trig))
	# return list of alarms
	return alarms

# set constants
CONTENTS_FILE = 'contents.xml'
CONFIG_FILE = './config.ini'
CAL_FILE = 'omnifocus-reminders-calgen.ics'

# parse config file
log('parsing config file')
config = configparser.ConfigParser()
if os.path.isfile(CONFIG_FILE):
	config.read(CONFIG_FILE)

# download files
log('downloading files:')
conn_options = None
basepath = None
client = None
contents_zip = None
if config.has_section('WEBDAV'):
	conn_options = {
		'webdav_hostname': config['WEBDAV']['hostname'],
		'webdav_login': config['WEBDAV']['username'],
		'webdav_password': config['WEBDAV']['sync_pass']
	}
	client = Client(conn_options)
	client.verify = True
	log('- downloading keystore')
	client.download_sync(remote_path=add_basepath('OmniFocus.ofocus/encrypted'), local_path='encrypted')
	log('- finding database')
	files = client.list(add_basepath('OmniFocus.ofocus/'))
	contents_zip = [file for file in files if file.endswith('.zip') and file.startswith('00')][0]
	# contents_zip = [file for file in files if file.endswith('.zip') and not file.startswith('00')][0]
	log('- downloading database')
	client.download_sync(remote_path=add_basepath('OmniFocus.ofocus/{}'.format(contents_zip)), local_path=contents_zip)

# decrypt them
log('decrypting database')
dec_contents_zip = None
if config.has_section('ENC') and 'is_encrypted' in config['ENC'] and config['ENC'].getboolean('is_encrypted') and contents_zip is not None:
	dec_contents_zip = 'dec_{}'.format(contents_zip)
	enc_pass = config['ENC']['enc_pass']
	encryptionMetadata = DocumentKey.parse_metadata(open('encrypted', 'rb'))
	metadataKey = DocumentKey.use_passphrase(encryptionMetadata, enc_pass)
	docKey = DocumentKey(encryptionMetadata.get('key').data, unwrapping_key=metadataKey)
	with open(contents_zip, "rb") as infp, open(dec_contents_zip, "wb") as outfp:
		docKey.decrypt_file(contents_zip, infp, outfp)

# unzip files
log('extracting database')
if zipfile is not None and zipfile.is_zipfile(dec_contents_zip):
	with zipfile.ZipFile(dec_contents_zip) as zf:
		zf.extractall()

# read in omnifocus database
log('reading database')
if not os.path.isfile(CONTENTS_FILE):
	print("that's not a file, dying")
	exit(1)
with open(CONTENTS_FILE) as fd:
	contents = xmltodict.parse(fd.read())

# look for tasks with due dates
log('searching database')
margin = datetime.timedelta(weeks = 4)
today = datetime.datetime.now(datetime.timezone.utc)
tasks_to_include = []
# figure out a way to tell if there's only one object in there
tasks_with_due = [task for task in contents['omnifocus']['task']
	if 'due' in task and task['due'] is not None]
for task in tasks_with_due:
	due_at = datealize(task['due'])
	if today <= due_at <= today + margin:
		tasks_to_include.append(task)

calendar = ics.Calendar()
for task in tasks_to_include:
	event = ics.Event()
	event.name = task['name']
	event.begin = task['due']
	if 'note' in task and task['note'] is not None:
		event.description = xmltodict.unparse(task['note'], full_document=False)
	if 'estimated-minutes' in task and task['estimated-minutes'] is not None:
		event.duration = datetime.timedelta(minutes = abs(int(task['estimated-minutes'])))
	event.url = 'omnifocus:///task/{}'.format(task['@id'])
	event.alarms = get_alarms(task)
	calendar.events.add(event)
	if should_log: pprint(event)
if should_log: pprint(calendar)

# write calendar
log('writing calendar to file')
with open(CAL_FILE, 'w') as fd:
	fd.writelines(calendar)

# upload files
log('uploading calendar to webdav')
if client is not None:
	client.upload_sync(local_path=CAL_FILE, remote_path=add_basepath(CAL_FILE))

# cleanup
log('cleaning up')
os.remove(CONTENTS_FILE)
os.remove('encrypted')
os.remove(dec_contents_zip)
os.remove(contents_zip)
# os.remove('CAL_FILE')
