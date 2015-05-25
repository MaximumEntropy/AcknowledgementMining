import pickle
import nltk
from nltk.corpus import stopwords
import string
import os
import sys
import re
DISTANCE_CUTOFF = 4
f = open('phrases.txt','r')
phrases = pickle.load(f)
phrases.append('gift of ??')
phrases.append('gifts of ??')
phrases.append('gift of the ??')
phrases.append('gifts of the ??')
phrases.append('providing ?? antibodies')
phrases.append('providing ?? antibody')
phrases.append('providing the ?? antibodies')
phrases.append('providing the ?? antibodies')
phrases.append('providing ??')
phrases.append('providing the ??')
unwanted_phrases = ['the ??','??']
phrases = [i for i in phrases if i not in unwanted_phrases]
f.close()
f = open('antibody_acknowledgement_sentences_format_fix_antibodies_null_3','r')
sentences = f.readlines()
g = open('removed_antibodies','w')
h = open('antibody_names','w')
h2 = open('donor_names','w')
h3 = open('affiliation_names','w')
f2 = open('papers_4','r')
h4 = open('results_excel_bootstrap.tsv','w')
papers = f2.readlines()
parent = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent + '/MITIE/mitielib')

punctuations = [punctuation for punctuation in string.punctuation]
stop_words = stopwords.words('english') + punctuations
from mitie import *
ner = named_entity_extractor('MITIE/MITIE-models/english/ner_model.dat')

unwated_candidates = stop_words + ['monoclonal','polyclonal','antibody','antibodies']

def get_anti_substring_words(sentence):
        anti_substring_words = [word for word in sentence if 'anti-' in word]
        return anti_substring_words

def remove_noisy_candidates(antibody_candidates):
        antibody_candidates = [candidate for candidate in antibody_candidates if candidate.lower() not in unwated_candidates]
        return list(set(antibody_candidates))

def get_antibody_candidate(sentence):
    candidates = []
    tags = []
    antibody_tags = ['monoclonal','polyclonal']
    for phrase in phrases:
        phrase = phrase.translate(None, ',.;:()')
        phrase = phrase.lower().split()
        phrase_position = 0
        new_word = ''
        for word in sentence:
            if phrase[phrase_position] == '??':
                new_word = word
                if phrase_position == len(phrase) - 1:
                    candidates.append(new_word)
                    if 'monoclonal' in phrase:
                        tags.append('monoclonal')
                    elif 'polyclonal' in phrase:
                        tags.append('polyclonal')
                    else:
                        tags.append('None')
                    phrase_position = 0
                    continue
                phrase_position += 1
            elif word == phrase[phrase_position]:
                if phrase_position == len(phrase) - 1:
                    candidates.append(new_word)
                    if 'monoclonal' in phrase:
                        tags.append('monoclonal')
                    elif 'polyclonal' in phrase:
                        tags.append('polyclonal')
                    else:
                        tags.append('None')
                    phrase_position = 0
                    continue
                phrase_position += 1
            else:
                phrase_position = 0
                new_word = ''
    return candidates

def get_antibody_donors(sentence,antibody_candidates,tokenized_sentence):
    if antibody_candidates == []:
            antibody_index = [ind for ind,word in enumerate(tokenized_sentence) if 'antibody' in word.lower()]
            antibodies_index = [ind for ind,word in enumerate(tokenized_sentence) if 'antibodies' in word.lower()]
            candidate_indexes = antibody_index + antibodies_index
    else:
        candidate_indexes = [ind for ind,word in enumerate(tokenized_sentence) if word.lower() in antibody_candidates]
    print 'Candidate Indexes : ' + str(candidate_indexes)
    tokens = nltk.word_tokenize(sentence)
    entities = ner.extract_entities(tokens)
    people = [entity for entity in entities if entity[1] == 'PERSON']
    affiliations = [entity for entity in entities if entity[1] == 'ORGANIZATION']
    people_xrange = [entity[0][-1] for entity in people]
    affiliations_xrange = [[" ".join(tokens[i] for i in entity[0]),entity[0][-1]] for entity in affiliations]
    people_xrange = [[" ".join(tokens[i] for i in entity[0]),entity[0][-1]] for entity in people]
    donor_list = []
    affiliation_list = []
    for candidate_location in candidate_indexes:
        closest_distance_person = 999999999
        closest_person = ''
        closest_person_start = 9999999
        if people_xrange == []:
            donor_list.append('None')
            affiliation_list.append('None')
        else:
            for person in people_xrange:
                if person[1] < candidate_location and (candidate_location - person[1]) < closest_distance_person:
                    closest_distance_person = candidate_location - person[1]
                    closest_person = person[0]
                    closest_person_start = person[1]
                closest_distance_affiliation = 99999999
                closest_affiliation = ''
                for affiliation in affiliations_xrange:
                    if affiliation[-1] > closest_person_start and affiliation[-1] < candidate_location and (affiliation[-1] - closest_person_start) < closest_distance_affiliation:
                        closest_distance_affiliation = affiliation[-1] - closest_person_start
                        closest_affiliation = affiliation[0]

                if closest_distance_affiliation < closest_distance_person:
                    if closest_distance_affiliation > DISTANCE_CUTOFF:
                        closest_affiliation = 'None'

                if closest_affiliation == '':
                    closest_affiliation = 'None'
                if closest_person == '':
                    closest_person = 'None'
            donor_list.append(closest_person)
            affiliation_list.append(closest_affiliation)

    return donor_list,affiliation_list

no_candidate_sentences = []
no_candidate_sentences_numbers = []
for sent_no,sentence in enumerate(sentences):
    sentence = sentence.strip()
    sentence = sentence.replace('Acknowledgments','')
    sentence = sentence.replace('ACKNOWLEDGMENTS','')
    sentence = sentence.replace('acknowledgments','')
    sentence = sentence.replace('Acknowledgements','')
    sentence = sentence.replace('ACKNOWLEDGEMENTS','')
    sentence = sentence.replace('acknowledgements','')
    sentence = sentence.replace('Acknowledgment','')
    sentence = sentence.replace('ACKNOWLEDGMENT','')
    sentence = sentence.replace('acknowledgment','')
    sentence = sentence.replace('Acknowledgement','')
    sentence = sentence.replace('ACKNOWLEDGEMENT','')
    sentence = sentence.replace('acknowledgement','')
    tokenized_sentence = nltk.word_tokenize(sentence.lower())
    print '=========================================================================='
    print 'Sentence : ' + str(tokenized_sentence)
    antibody_candidates = get_antibody_candidate(tokenized_sentence)
    antibody_candidates = remove_noisy_candidates(antibody_candidates)
    anti_substring_words = get_anti_substring_words(tokenized_sentence)
    antibody_candidates.extend(anti_substring_words)
    antibody_candidates = list(set(antibody_candidates))
    print 'Antibody Candidates : ' + str(antibody_candidates)
    sent_no = sent_no + 1
    if antibody_candidates == []:
        no_candidate_sentences.append(sentences)
        no_candidate_sentences_numbers.append(sent_no)  
    for candidate in antibody_candidates:
        h.write(candidate + '\t' + str(sent_no) + '\n')
    donor_candidates,affiliations = get_antibody_donors(sentence,antibody_candidates,tokenized_sentence)
    print 'Donor candidates & Affiliations : ' + str(donor_candidates) + '----> ' + str(affiliations)
    #print sent_no,donor_candidates
    if donor_candidates == []:
        h2.write('None' + '\t' + str(sent_no) + '\n')
    else:
        for candidate in donor_candidates:
                h2.write(candidate + '\t' + str(sent_no) + '\n')
    if affiliations == []:
        h3.write('None' + '\t' + str(sent_no) + '\n')
    else:
        for affiliation in affiliations:
                h3.write(affiliation + '\t' + str(sent_no) + '\n')
    paper = papers[sent_no].strip().split('\t')
    journal = paper[1]
    paper_details = paper[0]
    paper_details = paper_details.replace(journal,'')
    paper_year = paper_details.split('_')[1]
    #print len(antibody_candidates),len(donor_candidates),len(affiliations)
    for i in range(len(antibody_candidates)):
        try:
            h4.write(antibody_candidates[i] + '\t' + donor_candidates[i] + '\t' + affiliations[i] + '\t' + paper_year + '\t' + journal + '\t' + sentence)
            h4.write('\n')
        except IndexError:
            h4.write('None' + '\t' + donor_candidates[i] + '\t' + affiliations[i] + '\t' + paper_year + '\t' + journal + '\t' + sentence)
            h4.write('\n')
#print no_candidate_sentences_numbers,len(no_candidate_sentences_numbers)
