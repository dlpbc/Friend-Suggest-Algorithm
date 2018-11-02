# -*- encoding: utf-8 -*-
import os
import datetime

def parse_email_text(lines):
	reading_cc_email_addresses = False
	reading_to_email_addresses = False
	timestamp = None
	sender_email_address = ''
	to_email_addresses = ''
	cc_email_addresses = ''
	for line in lines:
		line = line.strip()
		if 'Date: ' in line:
			timestamp = line[6 : -12]
			continue
		if 'From: ' in line:
			sender_email_address += line[6 : ]
			continue
		if 'To: ' in line:
			to_email_addresses += line[4 : ]
			reading_to_email_addresses = True
			continue
		if reading_to_email_addresses == True and 'Subject: ' not in line:
			to_email_addresses += line
			continue
		if 'Subject: ' in line and reading_to_email_addresses == True:
			reading_to_email_addresses = False
			continue
		if 'Cc: ' in line:
			cc_email_addresses += line[4 : ]
			reading_cc_email_addresses = True
			continue
		if reading_cc_email_addresses == True and 'Mime-Version' not in line:
			cc_email_addresses += line
			continue
		if 'Mime-Version: ' in line:
			reading_cc_email_addresses = False
			break # done reading necessary data. no need to parse through the extra lines
	return [timestamp, sender_email_address, to_email_addresses, cc_email_addresses]

def load_data():
	user_email = 'sara.shackleton@enron.com'
	n_incoming_mails = 4393
	n_outgoing_mails = 4407

	incoming_folders = ['inbox', 'notes_inbox']
	outgoing_folders = ['sent', 'sent_items']

	base_path = 'dataset/'

    # a list to store all unique contacts (email-addresses)
    # from incoming and outgoing emails.
    # The list index of each contact is considered as the
    # contact id.
	all_contacts = []
	num_contacts = 0

	# A dictionary to store all groups the user interacted with.
	# In addition, it also stores the timestamp of each outgoing
	# and incoming interactions user and each group
	# each group is a four (4) element dictionary.
	# The first element in the tuple is a list that contains one or more contact ids.
	# The second element contains a list of timestamps of outgoing interactions.
	# The third element contains a list of timestamps of incoming interactions.
	# The fourth elemeent is the weight value specifying the strength of the connection
	#     between the user and the group. At this intial phase, the default value is -1.0
	# The key of each group is even as g_groupindex
	# Example: {
	#           'g_1': {'g_contacts': [4, 7, 90], 'Iout': [23423, 231123, ...], 'Iin': [23423, 231123, 235211], 'weight':-1.0}, 
	#           'g_2': {'g_contacts': [74], 'Iout': [23423, 231123, 235211,...], 'Iin': [23423,...], 'weight':-1.0}
	#          }
	groups = {}

	# outgoing mails.
	# 2209_, 5158_ multiple contacts
	# Date, To, Subject, CC:
	for out_folder in outgoing_folders:
		path = base_path + out_folder + '/'
		email_files = os.listdir(path)
		for email_file in email_files:
			lines = None
			with open(path + email_file, 'r') as f:
				lines = f.readlines()
			ret = parse_email_text(lines)
			timestamp = ret[0]
			to_email_addresses = ret[2]
			cc_email_addresses = ret[3]
			# convert date to POSIX/UNIX time stamp (in seconds since January 1, 1970, 00:00:00 (UTC))
			timestamp = datetime.datetime.strptime(timestamp, '%a, %d %b %Y %H:%M:%S').timestamp()
			# concatenate to_email_addresses and cc_email_addresses
			group_contacts = ', '.join([to_email_addresses, cc_email_addresses])
			# break concatenated receiver emails using split
			group_contacts = [email.strip() for email in group_contacts.split(',')] # list of email addresses
			group_contacts = [email for email in group_contacts if email is not ''] # remove any '' in the list
			# add receiver emails to contact list if they are not already part of the list
			for email in group_contacts:
				if email not in all_contacts:
					all_contacts.append(email)
			# convert group contacts from email address to corresponding index (integer)
			group_contacts = [all_contacts.index(email) for email in group_contacts] # list of index representative of email addresses
			group_contacts = set(group_contacts)
			# check whether group_contacts already exist in the group list
			group_exist = False
			for g_idx, g_info in groups.items():
				if len(group_contacts.symmetric_difference(set(g_info['g_contacts']))) == 0:
					group_exist = True
					break
			if group_exist:
				groups[g_idx]['Iout'].append(timestamp)
			else:
				num_groups = len(groups)
				new_idx = 'g_' + str(num_groups+1)
				groups[new_idx] = dict({'g_contacts': group_contacts, 'Iout': [timestamp], 'Iin':[], 'weight':-1.0})

	# incoming mails.
	# ex: 26_
	# Date, To, Subject, CC:
	for in_folder in incoming_folders:
		path = base_path + in_folder + '/'
		email_files = os.listdir(path)
		for email_file in email_files:
			lines = None
			with open(path + email_file, 'r') as f:
				lines = f.readlines()
			ret = parse_email_text(lines)
			timestamp = ret[0]
			sender_email_address = ret[1]
			to_email_addresses = ret[2]
			cc_email_addresses = ret[3]
			# convert date to POSIX/UNIX time stamp (in seconds since January 1, 1970, 00:00:00 (UTC))
			timestamp = datetime.datetime.strptime(timestamp, '%a, %d %b %Y %H:%M:%S').timestamp()
			# concatenate to_emails and cc_emails
			group_contacts = ', '.join([sender_email_address, to_email_addresses, cc_email_addresses])
			# break concatenated receiver emails using split
			group_contacts = [email.strip() for email in group_contacts.split(',')] # list of email addresses
			group_contacts = [email for email in group_contacts if email is not ''] # remove any '' in the list
			# since this is an incoming mail, the user's email address is part of the group contacts (i.e. 
			# as part of either `cc` email addresses or `to` email addresses).
			# Therefore remove user email address. Because when user is a receiver of the email, then
			# all other recepient contacts in the email and including the sender becomes a group
			# connected to the user.
			#assert user_email in group_contacts, 'an error occurred processing file ' + path + email_file
			if user_email in group_contacts:
				group_contacts.remove(user_email)

			# add receiver emails to contact list if they are not already part of the list
			for email in group_contacts:
				if email not in all_contacts:
					all_contacts.append(email)
			# convert group contacts from email address to corresponding index (integer)
			group_contacts = [all_contacts.index(email) for email in group_contacts] # list of index representative of email addresses
			group_contacts = set(group_contacts)

			# check whether group_contacts already exist in the group list
			group_exist = False
			for g_idx, g_info in groups.items():
				if len(group_contacts.symmetric_difference(set(g_info['g_contacts']))) == 0:
					group_exist = True
					break
			if group_exist:
				groups[g_idx]['Iin'].append(timestamp)
			else:
				num_groups = len(groups)
				new_idx = 'g_' + str(num_groups+1)
				groups[new_idx] = dict({'g_contacts': group_contacts, 'Iout': [], 'Iin':[timestamp], 'weight':-1.0})

	return [groups, all_contacts]
