import itertools
import enchant
import nltk
'''

Some basic rules :

1. If the word antibody is not explictly found on a pass, make another pass searching for antibody as a substring.
If a substring match is found, treat that as the antibody lexicon.

2. Search for NMOD of the antibody lexicon. That is the name of the antibody.

3. Search for keywords like thank. If there is more than one thank, traverse the dependency graph from antibody
see which "thank word" it matches and find the DOBJ of that and that should give you the person / affiliation

4. Action (providing, giving) can be got from the heads of the antibody lexicon

'''

class Parse:
    def __str__(self):
        return self.lex_id + self.word
    def __init__(self):
        self.lexicons = []
        self.dependency_graph = {}
        self.antibodymod = None
        pass
    def get_lexicon(self,lex_id):
        return [lexicon for lexicon in self.lexicons if lexicon.lex_id == lex_id][0]
    def get_children(self,lex_id):
        return [self.get_lexicon(lex_id) for lex_id in self.dependency_graph[lex_id]['Children']]
    def get_parent(self,lex_id):
        return [self.get_lexicon(lex_id) for lex_id in self.dependency_graph[lex_id]['Parent']]
    def get_lexicon_by_name(self,word):
        return [lexicon for lexicon in self.lexicons if lexicon.word == word][0]
    def generate_dependency_graph(self):
        self.dependency_graph = {}
        for lexicon in self.lexicons:
            lexicon_head = lexicon.head
            if lexicon_head not in self.dependency_graph:
                self.dependency_graph[lexicon_head] = {}
                self.dependency_graph[lexicon_head]['Parent'] = []
                self.dependency_graph[lexicon_head]['Children'] = [lexicon.lex_id]
            else:
                self.dependency_graph[lexicon_head]['Children'].append(lexicon.lex_id)
            if lexicon.lex_id not in self.dependency_graph:
                self.dependency_graph[lexicon.lex_id] = {}
                self.dependency_graph[lexicon.lex_id]['Parent'] = [lexicon.head]
                self.dependency_graph[lexicon.lex_id]['Children'] = []
            else:
                self.dependency_graph[lexicon.lex_id]['Parent'].append(lexicon.head)

    def get_root(self):
        head_lexicon = [lexicon for lexicon in self.lexicons if lexicon.head == '0']
        return head_lexicon[0]
    def get_antibody_lexicon(self):
        antibody_lexicon = [lexicon for lexicon in self.lexicons if lexicon.word.lower() == 'antibody']
        if antibody_lexicon == []:
            antibody_lexicon = [lexicon for lexicon in self.lexicons if 'antibody' in lexicon.word.lower()]
            return antibody_lexicon[0]
        return antibody_lexicon[0]
    def get_ack_words(self):
        acknowledgement_words = ['thank','grateful','thankful']
        ack_lexicon = [lexicon for lexicon in self.lexicons if lexicon.word.lower() in acknowledgement_words]
        return ack_lexicon

class Lexicon:
    def __init__(self):
        self.lex_id = None
        self.word = None
        self.lemma = None
        self.pos_tag = None
        self.feats = None
        self.head = None
        self.deprel = None

def get_antibody_name(parse_object):
    tags = ['monoclonal','polyclonal','primary','secondary']
    parse_object.generate_dependency_graph()
    dependency_graph = parse_object.dependency_graph
    antibody_lexicon = parse_object.get_antibody_lexicon()
    print antibody_lexicon.word
    depth_1_children = parse_object.get_children(antibody_lexicon.lex_id)
    antibody_tags = []
    antibody_words = []
    for child in depth_1_children:
        if child.deprel == 'NMOD' and not english_dict.check(child.word):
            antibody_words.append(child.word)
        elif child.deprel == 'NMOD' and child.word.lower() in tags:
            antibody_tags.append(child.word)
    if antibody_words != []:
        return antibody_tags,antibody_words

    depth_2_children = [parse_object.get_children(child.lex_id) for child in depth_1_children]
    flattened_list = sum(depth_2_children, [])
    for child in flattened_list:
        if (child.deprel == 'NMOD' or child.deprel == 'PMOD') and not english_dict.check(child.word):
            if child.word.lower() in tags:
                antibody_tags.append(child.word)
            else:
                antibody_words.append(child.word)
    return antibody_tags,antibody_words

def get_donor_name(parse_object,raw_sentence):
    # Get the ack word and search for Person Named Entities around it. Use Lex IDs to define distance (NE within 4 either side)
    # Priority to NEs on the right.
    ne_chunk_tree = nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(raw_sentence)))
    named_entities = []
    for subtree in ne_chunk_tree:
        if type(subtree) is nltk.tree.Tree:
            if subtree.label() == 'PERSON':
                named_entities.append(subtree.leaves()[0])
    print named_entities
    parse_object.generate_dependency_graph()
    dep_parse = parse_object.dependency_graph
    ack_lexicons = parse_object.get_ack_words()
    antibody_lexicon = parse_object.get_antibody_lexicon()
    if ack_lexicons == []:
        return []
    children = []
    for lexicon in ack_lexicons:
        children.append(dep_parse[lexicon.lex_id]['Children'])
    children = sum(children,[])
    objs = []
    children = [parse_object.get_lexicon(child) for child in children]
    conjs = []
    for child in children:
        if child.deprel == 'OBJ' and child.word[0].isupper():
            objs.append(child.word)
        if child.word == 'for':
            for_children = dep_parse[child.lex_id]['Children']
            print [parse_object.get_lexicon(item).word for item in for_children]
            for child in for_children:
                if child == antibody_lexicon.lex_id:
                    conjs.append(child)
    return objs,conjs

example_parses_path = '../PubMedCentral/FINAL_OUTPUT.txt'
example_sentences_path = '../PubMedCentral/antibody_acknowledgement_sentences_format_fix'
f = open(example_parses_path,'r')
g = open(example_sentences_path,'r')
contents = f.readlines()
english_dict = enchant.Dict("en_US")
parses = [list(x[1]) for x in itertools.groupby(contents, lambda x: x=='\n') if not x[0]]
sentences = g.readlines()
raw_sentences = []
for sentence in sentences:
    sentence = sentence.strip()
    sentence = sentence.replace('acknowledgements','')
    sentence = sentence.replace('Acknowledgements','')
    sentence = sentence.replace('ACKNOWLEDGEMENTS','')
    raw_sentences.append(sentence)
processed_parses = []
for parse in parses:
    new_parse = Parse()
    for line in parse:
        line = line.strip().split()
        try:
            new_lex = Lexicon()
            new_lex.lex_id = line[0]
            new_lex.word = line[1]
            new_lex.lemma = line[2]
            new_lex.pos_tag = line[3]
            new_lex.feats = line[4]
            new_lex.head = line[6]
            new_lex.deprel = line[7]
            new_parse.lexicons.append(new_lex)
        except IndexError:
            continue
    processed_parses.append(new_parse)

for raw_sentence,parse in zip(raw_sentences[900:1100],processed_parses[900:1100]):
    tags,antibody = get_antibody_name(parse)
    print raw_sentence
    print tags,antibody
    print '============================================'
    #print get_donor_name(parse,raw_sentence)
    #print '===================================='
    #print get_donor_name(parse)

print len(raw_sentences),len(processed_parses)