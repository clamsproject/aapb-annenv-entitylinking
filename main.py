"""Named Entity Linking annotation tool

Assumes:
- all annotations are extents
- no annotations with fragments

TODO to make this a working tool:
- add help function
- add backups
- connect annotations to the data
- allow more ways to browse annotations
- add way to fix mistakes

"""

import os
import pathlib
import lorem


SOUARCE_FILES = None
REPOSITORY = '../../clams-aapb-annotations/'
NER_ANNOTATIONS = REPOSITORY + 'uploads/2022-jun-namedentity/annotations/'
NEL_ANNOTATIONS = 'data.tab'


class CorpusEntities(object):

    def __init__(self, folder):
        self.folder = folder
        self.data = []
        self.idx = {}
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            file_annos = FileEntities(fname, fpath)
            self.data.append(file_annos)
            self.idx[fname] = file_annos

    def __getitem__(self, i):
        return self.data[i]

    def next(self):
        # TODO: this is rather brute force, keep a pointer
        for file_entities in self.data:
            for type_entity in file_entities.data.values():
                if type_entity.link is None:
                    return type_entity

    def add_annotation(self, annotation):
        file_entities = self.idx.get(annotation[0])
        entity = file_entities.data.get(annotation[1])
        entity.link = annotation[-1]

            
class FileEntities(object):

    def __init__(self, file_name, file_path):
        self.name = file_name
        self.path = file_path
        self.data = {}
        for line in open(file_path):
            entity = Entity(line)
            self.data.setdefault(entity.text, EntityType(file_name)).append(entity)

    def __str__(self):
        return "<FileEntities %s>" % len(self.data)

    def entity_type_count(self):
        return len(self.data)
        
    def entity_token_count(self):
        return sum([len(x) for x in self.data.values()])

    def status(self):
        done_types = 0
        done_tokens = 0
        for entity_type in self.data.values():
            if entity_type.link is not None:
                done_types += 1
                done_tokens += len(entity_type)
        percent_done_types = (done_types * 100 / self.entity_type_count())
        percent_done_tokens = (done_tokens * 100 / self.entity_token_count())
        return (self.name, percent_done_types, percent_done_tokens)

    def pp(self):
        print(self.name)
        for text in sorted(self.data):
            count = len(self.data[text])
            if count > 1:
                print("%3d  %s" % (count, text))


class EntityType(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self.tokens = []
        self.link = None

    def __str__(self):
        return ("<EntityType %s '%s' %s %s>"
                % (len(self), self.text(), self.entity_class(), self.link))

    def __getitem__(self, i):
        return self.tokens[i]

    def __len__(self):
        return len(self.tokens)

    def append(self, item):
        self.tokens.append(item)

    def text(self):
        return self.tokens[0].text

    def entity_class(self):
        return self.tokens[0].entity_class

        
class Entity(object):

    def __init__(self, line):
        (identifier, info, text) = line.strip().split('\t')
        entity_class, p1, p2 = info.split()
        if identifier[0] != 'T':
            print("WARNING, not an extent: %s" % line)
        self.text = text
        self.identifier = identifier
        self.entity_class = entity_class
        self.start = p1
        self.end = p2


class Annotator(object):

    def __init__(self, corpus_entities, annotations_file):
        self.corpus_entities = corpus_entities
        self.annotations_file = annotations_file
        self.annotations = []
        self.next_entity = None
        self.read_annotations()

    def read_annotations(self):
        pathlib.Path(self.annotations_file).touch(exist_ok=True)
        with open(self.annotations_file) as fh:
            for line in fh:
                # TODO: maybe do a sanity check here
                annotation = line.strip().split('\t')
                self.annotations.append(annotation)
                self.corpus_entities.add_annotation(annotation)
                
    def status(self):
        print("\nStatus on %s\n" % self.corpus_entities.folder)
        for file_entities in self.corpus_entities:
            (name, percent_done_types, percent_done_tokens) = file_entities.status()
            print('    %s %d %d' % (name, percent_done_types, percent_done_tokens))

    def loop(self):
        self.action = None
        while True:
            #print("action=[%s]\n" % self.action)
            if self.action in ('q', 'quit', 'exit'):
                break
            elif self.action in ('?', 'h', 'help'):
                self.action_help()
            elif self.action in ('s', 'status'):
                self.status()
            elif self.action in ('', 'n'):
                self.action_print_next()
            elif self.action == 'a':
                self.action_print_annotations()
            elif self.action is not None and self.action.startswith('a '):
                self.action_print_annotations(self.action[2:])
            elif self.action is not None:
                self.action_store_link()
                self.action_print_next()
            else:
                self.status()
            self.action = input("\n>>> ")

    def action_store_link(self):
        if self.next_entity is not None:
            self.next_entity.link = self.action
            # TODO: maybe add all the extent identifiers
            annotation = (self.next_entity.file_name,
                          self.next_entity.text(),
                          self.next_entity.entity_class(),
                          str(len(self.next_entity)),
                          self.action)
            #print(self.next_entity, annotation)
            self.annotations.append(annotation)
            with open(self.annotations_file, 'a') as fh:
                fh.write('%s\n' % '\t'.join(annotation))

    def action_print_next(self):
        self.next_entity = self.corpus_entities.next()
        text = self.next_entity.text()
        entity_class = self.next_entity.entity_class()
        print("\n%s[%s] (%s)%s\n" % (BOLD, text, entity_class, END))
        for i in range(len(self.next_entity)):
            left = lorem.sentence().lower()[:-1]
            right = lorem.sentence().lower()[:-1]
            print('    %50s  [%s%s%s]  %s' % (left, BLUE, text, END, right))

    def action_print_annotations(self, search_term=None):
        if search_term is None:
            print("\nCurrent annotations:\n")
            for annotation in self.annotations:
                print(annotation)
        else:
            print("\nAnnotations matching '%s':\n" % search_term)
            for annotation in self.annotations:
                if search_term.lower() in annotation[1].lower():
                    print(annotation)

    def action_help(self):
        print('\nAvailable commands:\n')
        print('? | h | help     -  this help message')
        print('q | quit | exit  -  quit the tool')
        print('s | status       -  show annotation status')
        print('n | <return>     -  show next entity to annotate')
        print('a                -  show list of all annotations')
        print('a <search-term>  -  show list of annotations that match <search-term>')
        print('\nCommands are typed in at the >>> prompt. If the prompt follows a print out')
        print('of an entity in context and a non-command is entered then the string that')
        print('was typed in is considered to be the entity link.')


BOLD = '\u001b[1m'
END = '\u001b[0m'
BLUE = '\u001b[34m'


if __name__ == '__main__':

    corpus_entities = CorpusEntities(NER_ANNOTATIONS)
    annotator = Annotator(corpus_entities, NEL_ANNOTATIONS)
    #entities[0].pp()
    #annotator.status()
    annotator.loop()
