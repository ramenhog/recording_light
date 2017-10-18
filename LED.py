import RPi.GPIO as GPIO
import os
import time
from time import sleep, strftime
from datetime import datetime
from subprocess import *
from subprocess import call
import re
from threading import Timer

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.parser import HeaderParser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.Utils import COMMASPACE, formatdate
from email import Encoders

end_queue = []

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)

GPIO.output(18, 0)
switch_state = False

def check_email():
	print 'Checking emails...'
	status, email_ids = imap_server.search(None, '(UNSEEN)')
	if email_ids == ['']:
		mail_list = []
	else:
		mail_list = get_subjects(email_ids)
	imap_server.close()
	return mail_list

def get_subjects(email_ids):
	subjects_list = []
	for e_id in email_ids[0].split():
		resp, data = imap_server.fetch(e_id, '(RFC822)')
		perf = HeaderParser().parsestr(data[0][1])
		subjects_list.append(perf['Subject'])
	return subjects_list

def user_code(mail_list, current_time):
	print mail_list
	print "You got mail!"
	for email_subject in mail_list:
		if email_subject.lower().find("studio:") != -1:
			subject_string = "".join(email_subject)
			trash, timestamps = subject_string.split("studio:")
			start,end = timestamps.split(",")
			start = re.sub('\-04:00$','',start)
			end = re.sub('\-04:00$','',end)
			time_format = '%Y-%m-%dT%H:%M:%S'
			start_dt = datetime.strptime(start, time_format)
			end_dt = datetime.strptime(end, time_format)

			if current_time <= end_dt:
				delta = end_dt - start_dt
				on_seconds = delta.total_seconds()
				end_queue.append(end_dt)
				print "Start: " + start
				print "End: " + end
				turn_on_light()
		elif email_subject.lower().find("light-on") != -1:
			turn_on_light()
		elif email_subject.lower().find("light-off") != -1:
			turn_off_light()

def turn_on_light():
	print "Turn light on"
	GPIO.output(18, GPIO.HIGH)
	global switch_state
	switch_state = True

def turn_off_light():
	print "Turn light off"
	GPIO.output(18, 0)
	global switch_state
	switch_state = False

while True:
	time.sleep(1)
	imap_server = imaplib.IMAP4_SSL("imap.gmail.com", 993)
	imap_server.login(USERNAME, PASSWORD)
	imap_server.select('INBOX')
	mail_list = check_email()
	current_time = datetime.now()
	if mail_list:
		user_code(mail_list, current_time)
	if switch_state:
		if len(end_queue) > 0:
			for end_time in end_queue:
				if current_time >= end_time:
					turn_off_light()
	else:
		end_queue = []
	sleep(1)
