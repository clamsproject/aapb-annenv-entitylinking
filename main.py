"""Named Entity Linking annotation tool

Requirements:
$ pip install requests==2.28.1

Assumes:
- all annotations are extents
- no annotations with fragments

Links are made to Wikipedia at https://en.wikipedia.org/wiki/Main_Page

For example:  https://en.wikipedia.org/wiki/Jim_Lehrer
But we only need to enter Jim_Lehrer

Location of source files and NER annotations:
- source files: https://github.com/clamsproject/wgbh-collaboration
- annotations: https://github.com/clamsproject/clams-aapb-annotations

These repositories should be cloned locally. Set the variables SOURCES_REPO and
ANNOTATIONS_REPO below to reflect the path to the local clone.

TODO: add backups
TODO: add way to fix mistakes
TODO: create one output file per input file
TODO: do we need to worry about languages?
TODO: allow entering "Jim Lehrer" instead of "Jim_Lehrer"
      (for validation we may need to use a different version as for saving)
TODO: change the confusing way the code deals with the different extensions
      (for sources we have .txt and for annotations we have.ann)

"""

import os
import copy
import pathlib
import collections
import datetime
import requests


# Locations of the source and annotation repositories, edit these as needed
SOURCES_REPO = '../../wgbh-collaboration/'
ANNOTATIONS_REPO = '../../clams-aapb-annotations/'

# No edits needed below this line

SOURCES = "%s/21" % SOURCES_REPO
ANNOTATIONS = '%s/uploads/2022-jun-namedentity/annotations/' % ANNOTATIONS_REPO
TOOL_OUTPUT = 'data/annotations.tab'

CONTEXT_SIZE = 40
PROMPT = 'ela>'


class Corpus(object):

    """A corpus which contains all files, it includes both the primary sources
    and the annotations.

    annotations_folder  -  location of the annotations
    sources_folder      -  location of the sources
    files               -  { filename => File }
    sources             -  { filename => file-content (str) }

    """

    def __init__(self, annotations_folder, sources_folder):
        self.annotations_folder = annotations_folder
        self.sources_folder = sources_folder
        self.files = {}
        self.sources = {}
        self._read_sources()
        self._read_annotations()
        self._add_dummy_file()

    def _read_sources(self):
        """Read all the primary sources. They are first stored on the Corpus
        instance and then later also imported into all File instances."""
        for fname in os.listdir(self.sources_folder):
            if len(fname) == 39:
                basename = os.path.splitext(fname)[0]
                fpath = os.path.join(self.sources_folder, fname)
                with open(fpath) as fh:
                    self.sources[basename] = fh.read()

    def _read_annotations(self):
        """Read the annotations over the primary sources. This is for the named
        entity annotations that are input to the linking process. Annotations
        are stored in File instance, which also get the source text added."""
        for fname in sorted(os.listdir(self.annotations_folder)):
            fpath = os.path.join(self.annotations_folder, fname)
            corpus_file = File(fname, fpath)
            basename = os.path.splitext(fname)[0]
            corpus_file.source = self.sources.get(basename, '')
            self.files[fname] = corpus_file

    def _add_dummy_file(self):
        first_file_name = 'cpb-aacip-507-154dn40c26-transcript.ann'
        dummy_file_name = 'cpb-aacip-000-0000000000-transcript.ann'
        first_file = self.files.get(first_file_name)
        dummy_file = File(dummy_file_name)
        # print('---', first_file)
        # print('---', dummy_file)
        for entity_text, entity_type in first_file.data.items():
            if len(entity_type) > 5:
                dummy_file.source = first_file.source
                dummy_entity = copy.deepcopy(entity_type)
                dummy_entity.file_name = dummy_file_name
                for token in dummy_entity:
                    token.file_name = dummy_file_name
                dummy_file.data[entity_type.text()] = dummy_entity
        self.files[dummy_file_name] = dummy_file

    def get_files(self):
        return [self.files[file_name] for file_name in sorted(self.files)]

    def next(self):
        # TODO: this is rather brute force, maybe keep a pointer
        for corpus_file in self.get_files():
            for type_entity in corpus_file.data.values():
                if type_entity.link is None:
                    return type_entity


class File(object):

    def __init__(self, file_name, file_path=None):
        self.name = file_name
        self.path = file_path
        self.source = None
        self.data = {}
        if file_path is not None:
            for line in open(file_path):
                entity = Entity(file_name, line)
                self.data.setdefault(entity.text, EntityType(file_name)).append(entity)

    def __str__(self):
        return "<File %s %s>" % (self.name, len(self.data))

    def entity_type_count(self):
        return len(self.data)
        
    def entity_token_count(self):
        return sum([len(x) for x in self.data.values()])

    def get_context(self, entity):
        def normalize(s: str):
            return s.replace('\n', ' ')
        p1 = entity.start
        p2 = entity.end
        left = normalize(self.source[p1-CONTEXT_SIZE:p1])
        right = normalize(self.source[p2:p2+CONTEXT_SIZE])
        return left, right

    def status(self):
        done_types = 0
        done_tokens = 0
        for entity_type in self.data.values():
            if entity_type.link is not None:
                done_types += 1
                done_tokens += len(entity_type)
        percent_done_types = (done_types * 100 / self.entity_type_count())
        percent_done_tokens = (done_tokens * 100 / self.entity_token_count())
        return self.name, percent_done_types, percent_done_tokens

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

    def pp(self):
        print(self)
        for token in self[:3]:
            print('   ', token)

        
class Entity(object):

    def __init__(self, file_name, line):
        (identifier, info, text) = line.strip().split('\t')
        entity_class, p1, p2 = info.split()
        if identifier[0] != 'T':
            print("WARNING, not an extent: %s" % line)
        self.file_name = file_name
        self.text = text
        self.identifier = identifier
        self.entity_class = entity_class
        self.start = int(p1)
        self.end = int(p2)

    def __str__(self):
        return ("<Entity %s '%s' %s %s %s>"
                % (self.entity_class, self.text, self.file_name, self.start, self.end))


class Annotator(object):

    def __init__(self, corpus: Corpus, annotations_file: str):
        self.corpus = corpus
        self.annotations_file = annotations_file
        self.annotations = []
        self.annotation_id = 0
        self.next_entity = None
        self.action = None
        self.link_suggestion = None
        self._load_annotations()

    def _load_annotations(self):
        pathlib.Path(self.annotations_file).touch(exist_ok=True)
        with open(self.annotations_file) as fh:
            for line in fh:
                # TODO: maybe do a sanity check here
                annotation = line.strip().split('\t')
                if len(annotation) != 7:
                    print('WARNING: unexpected annotation')
                    continue
                self.add_annotation(annotation)

    def add_annotation(self, annotation: list):
        self.annotation_id = max(self.annotation_id, int(annotation[0]))
        self.annotations.append(annotation)
        file_name, entity, link = annotation[2], annotation[3], annotation[6]
        corpus_file = self.corpus.files.get(file_name)
        corpus_file.data.get(entity).link = link

    def status(self):
        print("\nStatus on %s\n" % self.corpus.annotations_folder)
        # for file_entities in self.corpus_entities:
        for file_entities in self.corpus.get_files():
            (name, percent_done_types, percent_done_tokens) = file_entities.status()
            print('    %s %4d %3d%%' % (name,
                                        file_entities.entity_type_count(),
                                        percent_done_types))

    def loop(self):
        self.action = None
        self.link_suggestion = None
        while True:
            # print("action=[%s]\n" % self.action)
            if self.action in ('q', 'quit', 'exit'):
                break
            elif self.action in ('?', 'h', 'help'):
                print_help()
            elif self.action in ('s', 'status'):
                self.status()
            elif self.action in ('', 'n'):
                self.action_print_next()
            elif self.action == 'a':
                self.action_print_annotations()
            elif self.action == 'y':
                self.action_accept_hint()
                self.action_print_next()
            elif self.action is not None and self.action.startswith('a '):
                self.action_print_annotations(self.action[2:])
            elif self.action is not None and self.action.startswith('c '):
                self.action_set_context(self.action[2:])
            elif self.action is not None:
                self.action_store_link()
                self.action_print_next()
            else:
                self.status()
            self.action = input("\n%s " % PROMPT)

    def action_accept_hint(self):
        if self.next_entity is not None and self.link_suggestion is not None:
            self.next_entity.link = self.link_suggestion
            self.add_link(self.link_suggestion)

    def action_store_link(self):
        if self.next_entity is not None:
            if self.validate_link():
                self.next_entity.link = self.action
                self.add_link(self.action)
            else:
                print("\n%sWARNING: '%s' is not an entry in Wikipedia.%s"
                      % (RED, self.action, END))

    def add_link(self, link):
        self.annotation_id += 1
        annotation = [
            str(self.annotation_id),
            timestamp(),
            self.next_entity.file_name,
            self.next_entity.text(),
            self.next_entity.entity_class(),
            str(len(self.next_entity)),
            link]
        self.annotations.append(annotation)
        with open(self.annotations_file, 'a') as fh:
            fh.write('%s\n' % '\t'.join([str(a) for a in annotation]))

    def action_print_next(self):
        self.next_entity = self.corpus.next()
        text = self.next_entity.text()
        entity_class = self.next_entity.entity_class()
        print("\n%s[%s] (%s)%s\n" % (BOLD, text, entity_class, END))
        for entity in self.next_entity:
            corpus_file = self.corpus.files.get(entity.file_name)
            left, right = corpus_file.get_context(entity)
            left = (CONTEXT_SIZE-len(left)) * ' ' + left
            print('    %s[%s%s%s]%s' % (left, BLUE, text, END, right))
        self.link_suggestion = self.suggest_link(text)
        if self.link_suggestion:
            print('\nLink suggestion: %s' % self.link_suggestion)

    def action_set_context(self, context_size):
        global CONTEXT_SIZE
        try:
            n = int(context_size)
            CONTEXT_SIZE = n
        except ValueError:
            print('\nWARNING: context size has to be an integer, ignoring command')

    def action_print_annotations(self, search_term=None):

        def print_annotation(annotation):
            identifier = annotation[0]
            fname = "%s:%s" % (annotation[2][:-15], annotation[5])
            e_class, e_text, link = annotation[4], annotation[3], annotation[6]
            print("%4s %-30s %-15s  -  %-33s  ==>  %s"
                  % (identifier, fname, e_class, e_text, link))

        if search_term is None:
            print("\nCurrent annotations:\n")
            for annotation in self.annotations:
                print_annotation(annotation)
        else:
            print("\nAnnotations matching '%s':\n" % search_term)
            for annotation in self.annotations:
                if search_term.lower() in annotation[3].lower():
                    print_annotation(annotation)

    def validate_link(self):
        """A link entered by the user is okay if it is either '-' or longer than
        one character (to avoid hasty typos) and if occurs in Wikipedia."""
        if self.action == '-':
            return True
        if len(self.action) > 1:
            url = 'https://en.wikipedia.org/wiki/%s' % self.action
            response = requests.get(url)
            if response.status_code == 200:
                return True
        return False

    def suggest_link(self, entity_text):
        suggestions = []
        for corpus_file in self.corpus.get_files():
            suggestion = corpus_file.data.get(entity_text)
            if suggestion is not None and suggestion.link is not None:
                suggestions.append(suggestion.link)
        c = collections.Counter(suggestions)
        try:
            return c.most_common()[0][0]
        except IndexError:
            return None


def timestamp():
    dt = datetime.datetime.now()
    return "%04d-%02d-%02d %02d:%02d:%02d" % (dt.year, dt.month, dt.day,
                                              dt.hour, dt.minute, dt.second)


def print_help():
    with open('help.txt') as fh:
        print("\n%s" % fh.read().strip())


BOLD = '\u001b[1m'
END = '\u001b[0m'
BLUE = '\u001b[34m'
RED = '\u001b[31m'


if __name__ == '__main__':

    Annotator(Corpus(ANNOTATIONS, SOURCES), TOOL_OUTPUT).loop()
