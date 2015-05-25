import nltk
import os
import re
import pickle
f = open('antibody_acknowledgement_sentences_format_fix_antibodies_null_3','r')
sentences = f.readlines()

antibody_names = ['anti-IRF1',
                  'anti-IRF-7',
                  'anti-HCV core',
                  'E1',
                  'E2',
                  'anti-PIF-antibody',
                  'anti-Kar2',
                  'anti-Pom152p',
                  'T53-1',
                  'S5',
                  'anti-En',
                  'anti-Dll',
                  'anti-CD28',
                  'DT9',
                  'anti-GFAP',
                  'anti-tubulin',
                  'anti-HA',
                  'anti-GFP',
                  'anti-IMC1',
                  'anti-BiP',
                  'anti-dengue',
                  'anti-E',
                  'anti-ACP',
                  'anti-CD63',
                  'anti-PCNA',
                  'anti-PML',
                  'MAGE-A4',
                  'anti-NS1',
                  'anti-OmpA',
                  'anti-MBNL1',
                  'anti-Rad53',
                  'anti-ACRV1',
                  'anti-AMA1',
                  'anti-gB',
                  'anti-CD4',
                  'anti-CD8',]

def get_parsed_sentence(sentence,entity):
    executable_path = '/usr/local/Cellar/stanford-parser/3.4/bin/lexparser.sh'
    os.popen('echo "' + sentence + '" > stanfordtemp.txt')
    parser_out = os.popen(executable_path + ' stanfordtemp.txt').readlines()
    parser_out = [i.strip() for i in parser_out if len(i) != 1]
    bracketed_parse = " ".join([i.strip() for i in parser_out if i.strip()[0] == "("])
    indices = [root.start() for root in re.finditer('\(ROOT', bracketed_parse)]
    sentences = []
    for ind,index in enumerate(indices):
        if ind == len(indices) - 1:
            end = 9999
        else:
            end = indices[ind+1]
        sentences.append(bracketed_parse[index:end])
    try:
    	sentences = [nltk.Tree.fromstring(sent) for sent in sentences if entity in sent][0]
    except:
    	return []
    return sentences

grammar = "NP: {<DT>?<JJ>*<NN>}"
CONTEXT_SIZE = 4
left_contexts = []
right_contexts = []

def get_new_phrases(sentences,antibody_names):
	print antibody_names
	phrases = []
	for ind,sentence in enumerate(sentences):
		print '==============================================================================='
		print '==============================================================================='
		print '==============================================================================='
		print 'Sentence Number : ' + str(ind)
		print '==============================================================================='
		print '==============================================================================='
		print '==============================================================================='
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
		tokenized_sentence = nltk.word_tokenize(sentence)
		unique_tokenized_sentence = set(tokenized_sentence)
		unique_antibody_names = set(antibody_names)
		overlap = unique_tokenized_sentence & unique_antibody_names
		overlap = list(overlap)
		if overlap != []:
			for item in overlap:
				phrase = ''
				parsed_sentence = get_parsed_sentence(sentence,item)
				if parsed_sentence == []:
					continue
				for ind,subtree in enumerate(list(reversed(list(parsed_sentence.subtrees())))):
					if subtree.label() == 'NP' and ind >= 2 and item in subtree.leaves():
						phrase = subtree.leaves()
						break
				phrases.append(' '.join(phrase).replace(item,'??'))
	return phrases

def get_new_words(sentences,phrases):
	new_words = []
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
	    sentence = nltk.word_tokenize(sentence)
	    for phrase in phrases:
	        phrase = phrase.split()
	        phrase_position = 0
	        new_word = ''
	        for word in sentence:
	            if phrase[phrase_position] == '??':
	                new_word = word
	                if phrase_position == len(phrase) - 1:
	                    new_words.append(new_word)
	                    phrase_position = 0
	                    continue
	                phrase_position += 1
	            elif word == phrase[phrase_position]:
	                if phrase_position == len(phrase) - 1:
	                    new_words.append(new_word)
	                    phrase_position = 0
	                    continue
	                phrase_position += 1
	            else:
	                phrase_position = 0
	                new_word = ''
	new_words = list(set(new_words))
	return new_words

for i in range(3):

	phrases = get_new_phrases(sentences,antibody_names)
	new_words = get_new_words(sentences,phrases)
	antibody_names.extend(new_words)
	z1 = open('phrases_iter_' + str(i),'w')
	z2 = open('new_words_iter_' + str(i),'w')
	pickle.dump(antibody_names,z2)
	pickle.dump(phrases,z1)
