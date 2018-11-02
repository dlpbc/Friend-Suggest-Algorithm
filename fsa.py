# -*- encoding: utf-8 -*-

"""
Friend suggest algorithm
"""

import os
import sys
import math
import time
import datetime
import pprint
from data_loader import load_data
import random
import argparse

def intersecting_group_score(contact, seed, group):
	s1 = set(group['g_contacts'])
	s2 = set(seed)
	if len(s1.intersection(s2)) != 0:
		return group['weight'] # interactions rank of group
	else:
		return 0

def intersection_weighted_score(contact, seed, group, k=0.5):
	s1 = set(group['g_contacts'])
	s2 = set(seed)
	interactions_rank = group['weight'] # interactions rank of group
	return interactions_rank * (k * len(s1.intersection(s2)))

def intersection_group_count(contact, seed, group):
	s1 = set(group['g_contacts'])
	s2 = set(seed)
	if len(s1.intersection(s2)) != 0:
		return 1
	else:
		return 0

def top_contact_score(contact, seed, group):
	return group['weight'] # interactions rank of group

def update_score(contact, seed, group, score_func='intersecting_group_score'):
	score_func_types = ['intersecting_group_score', 
		'intersection_weighted_score', 
		'intersection_group_count', 
		'top_contact_score']

	if score_func not in score_func_types:
		raise ValueError('score_func can only be set to one of the following: {0}'.format(str(score_func_types)))

	if score_func == score_func_types[0]:
		# intersecting_group_score
		return intersecting_group_score(contact, seed, group)
	elif score_func == score_func_types[1]:
		# intersection_weighted_score
		return intersection_weighted_score(contact, seed, group)
	elif score_func == score_func_types[2]:
		# intersection_group_count
		return intersection_group_count(contact, seed, group)
	elif score_func == score_func_types[3]:
		# top_contact_score
		return top_contact_score(contact, seed, group)

'''
This algorithm is used to determine the weight
of edges between the user and its corresponding
contact groups. This is computed using three factors;
a. frequency - groups with which the user communicate
               frequently are more important than others
               which user communicate infrequently.
b. recency - groups with which the user communicated with
             recently are more important than others
             which user communicated with long ago.
c. direction - groups which user sends messages to are more
               important than others from which user receive
               message.

Arguments:
I: dictionary containg of incoming and outgoing email interactions.
recency_weight_decay: floating point parameter that determines the decay
                      of recency relevance of email over time. [0, 1]

wout: relative importance of outgoing versus incoming emails.

'''
def interactions_rank(I = {'Iout':[], 'Iin':[]}, recency_weight_decay=4.0, wout=1.0):
	# get current (unix) timestamp
	# TODO: fix later
	curr_timestamp = datetime.datetime(2001, 12, 31).timestamp()
	#curr_timestamp = time.time()

	out_score = 0
	for interaction_timestamp in I['Iout']:
		# datetime difference in terms of seconds
		time_diff = curr_timestamp - interaction_timestamp
		# datetime difference in terms of weeks
		time_diff = time_diff / (60 * 60 * 24 * 7)
		out_score += math.pow(0.5, (time_diff) / recency_weight_decay)
	in_score = 0
	for interaction_timestamp in I['Iin']:
		# datetime difference in terms of seconds
		time_diff = curr_timestamp - interaction_timestamp
		# datetime difference in terms of weeks
		time_diff = time_diff / (60 * 60 * 24 * 7)
		in_score += math.pow(0.5, (time_diff) / recency_weight_decay)	

	return (wout * out_score) + in_score


'''
Friend suggest algorithm for expanding seed set.

The algorithm analyses the user egocentric (implicit social graph)
and uses it to suggest contacts to add to the initial seed set given

Arguments:
user_graph: the user egocentric network that represented
            as an implicit social graph.

seed: intial list of contacts that forms part of the group to which more
      contact should be added.

Returns:
    a list of 2 element tuple. Each tuple contains contact information.
    The first element of the tuple is the contact id and the second 
    element of the tuple is the score assigned to the contact. The list
    is sorted based on the contact with the highest score.

'''
def fsa_expand_seed(user_graph, seed):
	# Example of a user egocentric network
	# Example: {
	#           'g_1': {'g_contacts': [4, 7, 90], 'Iout': [23423, 231123, ...], 'Iin': [23423, 231123, 235211], 'weight':-1.0}, 
	#           'g_2': {'g_contacts': [74], 'Iout': [23423, 231123, 235211,...], 'Iin': [23423,...], 'weight':-1.0}
	#          }

	G = user_graph # get groups
	# initially set the suggested contact list to empty.
	# the value assigned to each contact specifies the likelihood
	# of that the contact relates (or can be part of) the seed set
	# Thus expanding the seed set group.
	F = {}

	for g in G.values():
		for contact in g['g_contacts']:
			if contact in seed:
				continue

			if contact not in F:
				F[contact] = 0

			F[contact] += update_score(contact, seed, g)

	# sort (in descending order) the contact list based on
	# the value assigned to each contact. The contact with the
	# highest value implies that it has the highest likelihood
	# of the being added to the seed set.

	return sorted(F.items(), key=lambda x: x[1], reverse=True)

'''
Friend suggest algorithm for reducing contacts in a proposed group 
(contact list). It checks whether removing one the existing contacts
in the group will create a group with a higher score than the score 
of the initial list.

Arguments:
user_graph: the user egocentric network that represents
            an implicit social graph.

L: list of recipient of an email.

Return:
    a contact in `L` to remove or None if no suggested
    contact to remove.
'''
def fsa_remove_contact(user_graph, L):
	max_score = 0
	G = user_graph # get groups
	ret = is_a_group_in_egocentric_network(G, L)
	if ret is not None:
		max_score = ret[1]['weight']

	wrong_recipient = None
	for contact_id in L:
		# form a new contact list without current contact
		g = L.copy()
		g.remove(contact_id)
		ret = is_a_group_in_egocentric_network(G, g)
		if ret is not None:
			if group_info['weight'] > max_score:
				max_score = group_info['weight']
				wrong_recipient = contact_id
				break
	
	return wrong_recipient

'''
Checks whether the contact list `L` matches a group in a user egocentric
network `G`.

Arguments:
G: the user egocentric network that represents an implicit social graph

L: a list of contacts.

Return:
    None if L is not a group in G. Otherwise, return a two element tuple
    containing group id and group information (contact list, Iout, Iin, weight)
'''
def is_a_group_in_egocentric_network(G, L):
	for group_id, group_info in G.items():
		s1 = set(L)
		s2 = set(group_info['g_contacts'])
		if len(s1.symmetric_difference(s2)) == 0:
			return (group_id, group_info)
	return None

def main(user_email):
	# Step 1
	# Load the (user) email dataset
	# Focus only on email metadata
	# (timestamp, sender, and recipients)
	t1 = time.time()
	user_egocentric_network, user_contacts = load_data(user_email)
	t2 = time.time()
	print('loading user interactions...')
	print('time taken: {0}'.format(t2-t1))
	print('size of dataset: {0}'.format(sys.getsizeof(user_egocentric_network)))
	print('number of groups: {0}'.format(len(user_egocentric_network)))
	print('number of user contacts: {0}'.format(len(user_contacts)))

	# Step 2
	# compute weight of edge between user and each group

	# Example of a user egocentric network
	# {
	#     'g_1': {'g_contacts': [4, 7, 90], 'Iout': [23423, 231123, ...], 'Iin': [23423, 231123, 235211], 'weight':-1.0}, 
	#     'g_2': {'g_contacts': [74], 'Iout': [23423, 231123, 235211,...], 'Iin': [23423,...], 'weight':-1.0}
	# }
	#pprint.pprint(user_egocentric_network)
	print('\n***Computing interaction ranks for all groups...')
	for group_id in user_egocentric_network.keys():
		I = {'Iout': user_egocentric_network[group_id]['Iout'], 'Iin': user_egocentric_network[group_id]['Iin']}
		user_egocentric_network[group_id]['weight'] = interactions_rank(I, recency_weight_decay=5.0, wout=2.0)
	
	print('***Saving interactions rank for all groups to file: `{0}` ...'.format('interactions_rank_output.txt'))
	with open('interactions_rank_output.txt', 'w') as f:
		output = list(user_egocentric_network.items())
		output = ['{0}: {1}\n'.format(str(group_id), str(group_info['weight'])) for group_id, group_info in output]
		f.writelines(output)

	# Step 3
	# Run Friend Suggest Algorithm for expanding
	# initial seed set.
	print('\n***Friend suggest algorithm for expanding intial seed set of contact')
	n_contacts_in_seed_set = 2
	if n_contacts_in_seed_set > len(user_contacts):
		print('Error: number of contacts in the initial seed set should be less than total number of user\'s contacts')
		return

	seed = list(range(len(user_contacts)))
	random.shuffle(seed)
	seed = seed[ : n_contacts_in_seed_set] # initally, only 2 contacts in seed set.
	suggested_contacts = fsa_expand_seed(user_egocentric_network, seed)

	seed = [user_contacts[contact_id] for contact_id in seed]
	top_ten_suggestions = suggested_contacts[ : 10]
	top_ten_suggestions = [(user_contacts[contact_id], score) for contact_id, score in top_ten_suggestions]
	print('seed set: {0}\n'.format(str(seed)))
	print('top ten suggested contacts: ')
	pprint.pprint(top_ten_suggestions)

	# Step 4
	# Run Friend Suggest Algorithm for reducing
	# initial seed set. (i.e. selecting candidate contacts
	# in the seed set for removal)
	print('\n***Friend suggest algorithm for reducing intial seed set of contact')
	n_contacts_in_seed_set = 7
	if n_contacts_in_seed_set > len(user_contacts):
		print('Error: number of contacts in the initial seed set should be less than or equal to the total number of user\'s contacts')
		return

	seed = list(range(len(user_contacts)))
	random.shuffle(seed)
	seed = seed[ : n_contacts_in_seed_set] # initally, seven contacts in seed set
	contacts_to_remove = fsa_remove_contact(user_egocentric_network, seed)

	seed = [user_contacts[contact_id] for contact_id in seed]
	if contacts_to_remove is not None:
		contacts_to_remove = [user_contacts[contact_id] for contact_id in contacts_to_remove]
	print('seed set: \n{0}\n'.format(str(seed)))
	print('contacts to remove: \n{0}'.format(str(contacts_to_remove)))


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('email_address', help='user email address', type=str)
	args = parser.parse_args()
	main(args.email_address)
