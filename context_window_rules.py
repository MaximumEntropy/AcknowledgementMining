import enchant
import nltk
import re
import io
import os
import sys
CONTEXT_WINDOW = 4
CONTEXT_WINDOW_DONOR = 8
DISTANCE_CUTOFF = 50
antibody_aliases = ['antibody','antibody.','Antibody','antibodies']
example_sentences_path = '../PubMedCentral/antibody_acknowledgement_sentences_format_fix'
f = io.open(example_sentences_path,'r',encoding='utf8')
contents = f.readlines()
english_dict = enchant.Dict("en_US")
antibody_tags = ['primary','secondary','monoclonal','polyclonal']
parent = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent + 'MITIE/mitielib')

g = open('results.txt','w')

def remove_names_from_candidates(candidates):
	digits = re.compile('\d')
	
	'''

	1. If there is a dot, remove the candidate (P., Dr., Drs. etc)

	2. If the word starts with caps and the rest are all small alphabets then remove & no digits.

	'''
	
	new_candidates = []
	for candidate in candidates:
		if '.' in candidate:
			continue
		elif candidate[0].isupper() and not bool(digits.search(candidate)) and candidate[1:].islower():
			continue
		new_candidates.append(candidate)
	return new_candidates


def get_antibody_candidates(sentence):
	words = nltk.word_tokenize(sentence)
	antibody_words = []
	antibody_contexts_left = []
	antibody_contexts_right = []
	word_count = 0
	for word in words:
		if 'antibody' in word.lower():
			antibody_words.append(word)
			antibody_contexts_left.append(words[word_count-CONTEXT_WINDOW:word_count])
			antibody_contexts_right.append(words[word_count:word_count+CONTEXT_WINDOW])
		word_count += 1
	candidates = []
	tags = []	
	for context in antibody_contexts_left:
		found_flag = False
		for word in list(reversed(context)):
			if word in antibody_tags:
				tags.append(word) 
		for word in list(reversed(context)):
			if not english_dict.check(word) and word not in tags:
				candidates.append(word)
				found_flag = True
				continue
			if found_flag == True:
				break
	if candidates == []:
		for context in antibody_contexts_right:
			found_flag = False
			for word in context:
				if word in antibody_tags:
					tags.append(word) 
			for word in list(reversed(context)):
				if not english_dict.check(word) and word not in tags:
					candidates.append(word)
					found_flag = True
					continue
				if found_flag == True:
					break
	candidates = remove_names_from_candidates(candidates)
	return candidates,tags


def remove_antibodies_from_donor(candidates,antibody_candidates):
	'''

	Note: this function also removes the POS tags and concatenates names

	'''

	new_donor_candidates = []
	#candidates = sum(candidates,[])
	for candidate in candidates:
		found_flag = False
		for word in candidate:
			if word[0] in antibody_candidates:
				found_flag = True
				break
		if found_flag == True:
			continue
		name = ''
		for word in candidate:
			name += word[0] + ' '
		name = name[:-1]
		new_donor_candidates.append(name)
	return new_donor_candidates

def get_people(ner_sentence):
	entities = re.findall(r"\[(.*?)\]",ner_sentence)
	people_entities = []
	for entity in entities:
		if 'PERSON' in entity:
			people_entities.append(entity[7:])
	return people_entities

def get_affiliations(ner_sentence):
	entities = re.findall(r"\[(.*?)\]",ner_sentence)
	affiliation_entities = []
	for entity in entities:
		if 'ORGANIZATION' in entity:
			affiliation_entities.append(entity[13:])
	return affiliation_entities

def get_antibody_donor_candidates_ie(sentence):
	g = os.popen('echo "' + sentence + '" | MITIE/./ner_stream MITIE/MITIE-models/english/ner_model.dat')
	results = g.read()
	people = get_people(results)
	affiliations = get_affiliations(results)
	antibody_start = sentence.lower().find('antibody')
	people_xrange = []
	for person in people:
		people_xrange.append([person,sentence.find(person)+len(person)])
	affiliation_xrange = []
	for affiliation in affiliations:
		loc = sentence.find(affiliation)
		if loc == -1:
			continue
		affiliation_xrange.append([affiliation,loc+len(affiliation)])
	#print antibody_start,people_xrange,affiliation_xrange
	closest_distance_person = 999999999
	closest_person = ''
	closest_person_start = 9999999
	for person in people_xrange:
		if person[1] < antibody_start and (antibody_start - person[1]) < closest_distance_person:
			closest_distance_person = antibody_start - person[1]
			closest_person = person[0]
			closest_person_start = person[1]
	closest_distance_affiliation = 99999999
	closest_affiliation = ''
	for affiliation in affiliation_xrange:
		print affiliation[-1],antibody_start,closest_distance_affiliation,closest_affiliation
		if affiliation[-1] > closest_person_start and affiliation[-1] < antibody_start and (affiliation[-1] - closest_person_start) < closest_distance_affiliation:
			closest_distance_affiliation = affiliation[-1] - closest_person_start
			closest_affiliation = affiliation[0]
	'''
	if closest_distance_affiliation < closest_distance_person:
		print 'Affiliation closer than person.'
		if closest_distance_affiliation > DISTANCE_CUTOFF:
			closest_affiliation = 'None'
	'''
	'''
	else:
		print 'Person closer than affiliation'
		closest_distance_person = closest_distance_person - len(closest_person)
		if closest_distance_affiliation - closest_distance_person > DISTANCE_CUTOFF:
			closest_affiliation = 'None'
	'''
	#print closest_distance_person,closest_distance_affiliation
	#print 'Donor : ' + closest_person + ' Affiliation : ' + closest_affiliation
	#print sentence
	return closest_person,closest_affiliation

def get_antibody_donor_candidates(sentence,antibody_candidates):
	named_entity_chunk = nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sentence)))
	named_entity_chunk = list(named_entity_chunk)
	antibody_contexts_left = []
	antibody_contexts_right = []
	word_count = 0
	for entity in named_entity_chunk:
		if type(entity) is nltk.tree.Tree:
			continue
		if 'antibody' in entity[0].lower():
			antibody_contexts_left.append(named_entity_chunk[:word_count])
			antibody_contexts_right.append(named_entity_chunk[word_count+1:])
		word_count += 1
	candidates = []
	affiliations = []
	for context in antibody_contexts_left:
		for item in list(reversed(context)):
			if type(item) is nltk.tree.Tree:
				if item.label() == 'PERSON':
					candidates.append(item.leaves())
				elif item.label() == 'ORGANIZATION':
					affiliations.append(item.leaves())
	
	if candidates == []:
		for context in antibody_contexts_right:
			for item in context:
				if type(item) is nltk.tree.Tree:
					if item.label() == 'PERSON':
						candidates.append(item.leaves())
					elif item.label() == 'ORGANIZATION':
						affiliations.append(item.leaves())
	
	candidates = remove_antibodies_from_donor(candidates,antibody_candidates)
	print candidates
	if candidates == []:
		candidate = 'None'
	else:
		candidate = candidates[0]
	if affiliations == []:
		affiliation = 'None'
	else:
		affiliation = affiliations[0]
	#print candidate,affiliation
	return candidate,affiliation

for sentence in contents:
	sentence = sentence.strip()
	sentence = sentence.replace('Acknowledgements','')
	sentence = sentence.replace('ACKNOWLEDGEMENTS','')
	sentence = sentence.replace('acknowledgements','')
	donor_candidate,affiliation = get_antibody_donor_candidates_ie(sentence)
	antibody_candidates,tags = get_antibody_candidates(sentence)
	'''
	donor_candidate,affiliation = get_antibody_donor_candidates(sentence,antibody_candidates)
	#print antibody_candidates,tags
	#print donor_candidates,affiliations
	#print '================================================'
	#print donor_candidate
	if donor_candidate == []:
		donor_candidate = 'None'
	print donor_candidate,antibody_tag,antibody_name
	
	print output_sentence
	print sentence
	#print nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sentence)))
	print '==========================================='
	#print antibody_contexts_left
	#print antibody_contexts_right
	#print '=========================================='
	'''
	if antibody_candidates == []:
		continue
	antibody_name = ''
	for candidate in antibody_candidates:
		antibody_name += candidate + ' '
	antibody_name = antibody_name[:-1]
	if tags == []:
		antibody_tag = ' '
	else:	
		antibody_tag = ' ' + tags[0] + ' '
	output_sentence =  donor_candidate + ' (' + affiliation + ')' ' donated' + antibody_tag + antibody_name + ' antibody'
	print donor_candidate,affiliation
	g.write(output_sentence)
	g.write('\n')