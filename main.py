"""Named Entity Linking annotation tool

Requirements:
$ pip install requests==2.28.1

Starting the tool:
$ python main.py [--debug] [--demo]

With debugging the tool works the same but will print messages to the
standard output. In demo mode a small file is added for demo purposes.

Assumes:
- all annotations are extents
- no annotations with fragments

Links are made to Wikipedia at https://en.wikipedia.org/wiki/Main_Page, for
example: https://en.wikipedia.org/wiki/Jim_Lehrer. But we only need to enter
Jim_Lehrer, not the whole string.

Location of source files and NER annotations:
- source files: https://github.com/clamsproject/wgbh-collaboration
- annotations: https://github.com/clamsproject/clams-aapb-annotations

These repositories should be cloned locally. Set the variables SOURCES and
ANNOTATIONS below to reflect the paths into the local clones.

"""

# TODO: do we need to worry about languages?
# TODO: allow entering "Jim Lehrer" instead of "Jim_Lehrer"
#       (for validation we may need to use a different version as for saving)
# TODO: change the confusing way the code deals with the different extensions
#       (for sources we have .txt and for annotations we have.ann)


import os
import sys
import shutil
import copy
import pathlib
import collections
import datetime

import requests


# Locations of the source and entity annotation repositories, edit as needed
SOURCES = '../../wgbh-collaboration/21'
ENTITIES = '../../clams-aapb-annotations/uploads/2022-jun-namedentity/annotations'

# No edits should be needed below this line

ANNOTATIONS = 'data/annotations.tab'
ANNOTATIONS_BACKUP = 'data/annotations-%s.tab'

CONTEXT_SIZE = 40
PROMPT = 'bela>'
DEBUG = False
DEMO = False


class Warnings(object):
    NO_ENTITY = 'no entity was selected, type "n" to select next entity'
    UNKNOWN_COMMAND = 'unknown command, type "h" to see available commands'
    NO_LINK_SUGGESTION = 'there was no link suggestion'
    NOT_IN_WIKIPEDIA = "'%s' is not an entry in Wikipedia"


class Corpus(object):

    """A corpus containing all files, it includes both the primary sources
    and the annotations.

    annotations_folder  -  location of the annotations
    sources_folder      -  location of the sources
    files               -  { filename => File }
    sources             -  { filename => file-content: str }

    """

    def __init__(self, annotations_folder: str, sources_folder: str):
        """Create a corpus from a set of sources and a set of annotations."""
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
        are stored in File instances, which also get the source text added."""
        for fname in sorted(os.listdir(self.annotations_folder)):
            fpath = os.path.join(self.annotations_folder, fname)
            corpus_file = File(fname, fpath)
            basename = os.path.splitext(fname)[0]
            corpus_file.source = self.sources.get(basename, '')
            self.files[fname] = corpus_file

    def _add_dummy_file(self):
        """Create a dummy file from an existing file, using only the most common
        entities from the existing file. Then add it to the beginning of the file
        list. This is for demonstrating the tool."""
        if DEMO:
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
        """Return all File instances in the corpus, sorted on the filename."""
        return [self.files[file_name] for file_name in sorted(self.files)]

    def next(self):
        """Return the first un-annotated entity."""
        # TODO: this is rather brute force, maybe keep a pointer
        for corpus_file in self.get_files():
            for type_entity in corpus_file.data.values():
                if type_entity.link is None:
                    return type_entity


class File(object):

    """Stores all annotations for a file as well as the text source.

    name: str    -  the file name
    path: str    -  the relative path to the file
    source: str  -  source text for the file
    data: dict   -  { entity-text => EntityType }

    """

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
        """Return the number of entities in the file."""
        return len(self.data)
        
    def entity_token_count(self):
        """Return the number of entity tokens in the file."""
        return sum([len(x) for x in self.data.values()])

    def get_context(self, entity) -> tuple:
        """Return the left and right context of the entity."""
        def normalize(s: str):
            return s.replace('\n', ' ')
        p1 = entity.start
        p2 = entity.end
        left = normalize(self.source[p1-CONTEXT_SIZE:p1])
        right = normalize(self.source[p2:p2+CONTEXT_SIZE])
        return left, right

    def status(self) -> tuple:
        """Return the percentages done for entity types and tokens."""
        done_types = 0
        done_tokens = 0
        for entity_type in self.data.values():
            if entity_type.link is not None:
                done_types += 1
                done_tokens += len(entity_type)
        percent_done_types = (done_types * 100 / self.entity_type_count())
        percent_done_tokens = (done_tokens * 100 / self.entity_token_count())
        return percent_done_types, percent_done_tokens

    def pp(self):
        print(self.name)
        for text in sorted(self.data):
            count = len(self.data[text])
            if count > 1:
                print("%3d  %s" % (count, text))


class Entity(object):

    """An entity instance, corresponding to an annotation.

    identifier: str    -  identifier of the entity annotation
    file_name: str     -  name of the file
    text: str          -  text extent of the entity
    entity_class: str  -  class of the entity (person, location, etcetera)
    start: int         -  start offset of the entity
    end: int           -  end offset of the entity

    """

    def __init__(self, file_name, line):
        """Create an Entity from a line in an annotation file."""
        (identifier, info, text) = line.strip().split('\t')
        entity_class, p1, p2 = info.split()
        if identifier[0] != 'T':
            print("WARNING, not an extent: %s" % line)
        self.identifier = identifier
        self.file_name = file_name
        self.text = text
        self.entity_class = entity_class
        self.start = int(p1)
        self.end = int(p2)

    def __str__(self):
        return ("<Entity %s '%s' %s %s %s>"
                % (self.entity_class, self.text, self.file_name, self.start, self.end))


class EntityType(object):

    """Contains all occurrences of an entity and the link created for it (which
    is equal to None initially) for a single annotation file. The assumption is
    that several occurrence of the same string in a file will have the same
    grounding in Wikipedia.

    file_name: str  -  name of the file
    tokens: list    -  List of instances of Entity
    link: str       -  the link

    """

    def __init__(self, file_name):
        """Initialize with just the filename, the tokens list starts off empty
        and the link is set to None."""
        self.file_name = file_name
        self.tokens = []
        self.link = None

    def __str__(self):
        return ("<EntityType %s '%s' %s %s>"
                % (len(self), self.text(), self.entity_class(), self.link))

    def __getitem__(self, i) -> Entity:
        return self.tokens[i]

    def __len__(self) -> int:
        """The length of an Entity is the number of entity tokens in it."""
        return len(self.tokens)

    def append(self, item: Entity):
        """Append the Entity to the token list."""
        self.tokens.append(item)

    def text(self) -> str:
        """The text of the entity, taken from the first token."""
        return self.tokens[0].text

    def entity_class(self) -> str:
        """The class of the entity, taken from the first token."""
        return self.tokens[0].entity_class

    def pp(self):
        print(self)
        for entity in self.tokens[:3]:
            print('   ', entity)


class LinkAnnotation(object):

    """The link annotation of an EntityType, referring to an entry in Wikipedia.

    is_valid: bool     -  True if the instance is complete
    identifier: int    -  identifier of the entity type, starting at 1
    timestamp: str     -  timestamp in "YYYY-MM-DD hh:mm:ss" format
    file_name: str     -  the file the entity type occurs in
    text: str          -  the text string of the entity type
    entity_class: str  -  the class of the entity (person, etcetera)
    tokens: int        -  number of entity tokens in the type
    link: str          -  the link to Wikipedia

    The link is not a full Wikipedia link but just the last part of it, so
    instead of "https://en.wikipedia.org/wiki/Jim_Lehrer" we have "Jim_Lehrer".

    The entity_class and tokens variables are strictly not needed since you can
    get them from the entity type, they are in here for convenience.

    """

    def __init__(self, line):
        """Always initialize from a line with tab-separated fields."""
        # TODO: maybe do a sanity check here
        fields = line.strip().split('\t')
        self.is_valid = True if len(fields) == 7 else False
        self.identifier = int(fields[0])
        self.timestamp = fields[1]
        self.file_name = fields[2]
        self.text = fields[3]
        self.entity_class = fields[4]
        self.tokens = int(fields[5])
        self.link = fields[6]

    def __str__(self):
        return "<LinkAnnotation %s %s '%s' '%s'>" \
               % (self.identifier, self.file_name, self.text, self.link)

    def fields(self):
        """Returns the values of all instance variables in a fixed order."""
        return (self.identifier, self.timestamp, self.file_name, self.text,
                self.entity_class, self.tokens, self.link)

    def as_pretty_line(self):
        """Returns a line for pretty printing in the tool."""
        identifier = self.identifier
        fname = "%s:%s" % (self.file_name[:-15], self.tokens)
        e_class, e_text, link = self.entity_class, self.text, self.link
        return ("%4s %-30s %-17s  -  %-33s  ==>  %s"
                % (identifier, fname, e_class, e_text, link))

    def as_tab_separated_line(self):
        """Returns a line that can be used for storage in the annotation file."""
        return '%s' % '\t'.join([str(f) for f in self.fields()])


class LinkAnnotations(object):

    """Keep track of all the link annotations. A link annotation is a list with
    seven elements: identifier, timestamp, file name, entity text, entity class,
    number of tokens for the entity, and the entity link.

    corpus: Corpus         -  Corpus that the annotations are over
    annotations: list      -  list of instances of LinkAnnotation
    annotation_id: int     -  keeps track of identifier for the next annotation
    annotations_file: str  -  file with all saved annotations

    """

    def __init__(self, corpus: Corpus, annotations_file: str):
        """Initialize from a Corpus and the standard annotations file with
        previously saved annotations."""
        self.corpus = corpus
        self.annotations = []
        self.annotation_id = 0
        self.annotations_file = annotations_file
        self._load_annotations()

    def __getitem__(self, item):
        return self.annotations[item]

    def _load_annotations(self):
        pathlib.Path(self.annotations_file).touch(exist_ok=True)
        with open(self.annotations_file) as fh:
            for line in fh:
                annotation = LinkAnnotation(line)
                if annotation.is_valid:
                    self.add_annotation(annotation)

    def add_annotation(self, annotation: LinkAnnotation):
        """Add a link annotation to the list of annotations and to the entity
        that it is created for."""
        self.annotation_id = max(self.annotation_id, annotation.identifier)
        self.annotations.append(annotation)
        corpus_file = self.corpus.files.get(annotation.file_name)
        corpus_file.data.get(annotation.text).link = annotation.link

    def get_annotation(self, identifier: int):
        """Return None or the annotation that matches the identifier."""
        for a in self.annotations:
            if a.identifier == identifier:
                return a
        return None

    def add_link(self, entity, link):
        """Create an instance of LinkAnnotation and save it."""
        annotation_list = self.create_link(link, entity=entity)
        annotation_str = '\t'.join([str(f) for f in annotation_list])
        annotation_obj = LinkAnnotation(annotation_str)
        self.save_annotation(annotation_obj)

    def create_link(self, link, entity=None, annotation=None):
        """Create a new link annotation. If an existing annotation is handed in
        we use that to set some of the new annotation's values, otherwise we use
        the information from the current entity."""
        self.annotation_id += 1
        anno_id = str(self.annotation_id)
        ts = timestamp()
        (fname, text, e_class, e_len) = (None, None, None, None)
        if entity is not None:
            (fname, text, e_class, e_len) = \
                (entity.file_name, entity.text(),
                 entity.entity_class(), str(len(entity)))
        elif annotation is not None:
            annotation: LinkAnnotation
            (fname, text, e_class, e_len) = \
                (annotation.file_name, annotation.text,
                 annotation.entity_class, annotation.tokens)
        return [anno_id, ts, fname, text, e_class, e_len, link]

    def save_annotation(self, annotation: LinkAnnotation):
        """Append the annotation to the annotations list and write it to the
        annotations file."""
        self.annotations.append(annotation)
        with open(self.annotations_file, 'a') as fh:
            fh.write('%s\n' % annotation.as_tab_separated_line())

    def backup(self):
        source_file = self.annotations_file
        target_file = ANNOTATIONS_BACKUP % timestamp().replace(' ', ':')
        print('\nCopying %s to %s' % (source_file, target_file))
        shutil.copyfile(source_file, target_file)


class Annotator(object):

    """The annotation tool itself. Controls all user interactions and delegates
    the work of adding annotations to the embedded LinkAnnotations instance.

    corpus: Corpus                -  the corpus that the annotator runs on
    next_entity: EntityType       -  the next entity to be annotated
    action: str                   -  user provided action
    link_suggestion: str          -  a link suggestion generated by the tool
    annotations: LinkAnnotations  -  all annotations generated so far

    """

    def __init__(self, corpus: Corpus, annotations_file: str):
        self.corpus = corpus
        self.action = None
        self.next_entity = None
        self.link_suggestion = None
        self.annotations = LinkAnnotations(corpus, annotations_file)

    def loop(self):
        self.action = None
        self.link_suggestion = None
        while True:
            self.debug_loop('START OF LOOP:')
            if self.action in ('q', 'quit', 'exit'):
                break
            elif self.action is None:
                self.status()
            elif self.action in ('?', 'h', 'help'):
                self.print_help()
            elif self.action in ('s', 'status'):
                self.status()
            elif self.action in ('b', 'backup'):
                self.action_backup()
            elif self.action in ('', 'n'):
                self.action_print_next()
            elif self.action == 'a':
                self.action_print_annotations()
            elif self.action == 'y':
                self.action_accept_hint()
            elif self.action.startswith('f '):
                self.action_fix_link(self.action[2:])
            elif self.action.startswith('a '):
                self.action_print_annotations(self.action[2:])
            elif self.action.startswith('c '):
                self.action_set_context(self.action[2:])
            elif self.action == 'l':
                self.action_store_link('-')
            elif self.action.startswith('l '):
                self.action_store_link(self.action[2:])
            else:
                self.print_warning(Warnings.UNKNOWN_COMMAND)
            self.debug_loop('END OF LOOP, BEFORE PROMPT:')
            self.action = input("\n%s " % PROMPT).strip()

    def action_backup(self):
        self.annotations.backup()

    def action_accept_hint(self):
        if self.next_entity is None:
            self.print_warning(Warnings.NO_ENTITY)
        elif self.link_suggestion is None:
            self.print_warning(Warnings.NO_LINK_SUGGESTION)
            self.action_print_next()
        else:
            self.next_entity.link = self.link_suggestion
            self.annotations.add_link(self.next_entity, self.link_suggestion)
            self.action_print_next()

    def action_store_link(self, link):
        if self.next_entity is not None:
            if self.validate_link(link):
                self.next_entity.link = link
                self.annotations.add_link(self.next_entity, link)
            else:
                self.print_warning(Warnings.NOT_IN_WIKIPEDIA % link)
            self.action_print_next()
            if DEBUG:
                for a in self.annotations[-5:]:
                    print(a)
        else:
            self.print_warning(Warnings.NO_ENTITY)

    def action_fix_link(self, identifier_and_link):
        identifier, *link = identifier_and_link.split()
        identifier = int(identifier)
        link = ' '.join(link)
        if self.validate_link(link):
            old_annotation = self.annotations.get_annotation(identifier)
            new_annotation = self.annotations.create_link(link, annotation=old_annotation)
            new_annotation = LinkAnnotation('\t'.join([str(f) for f in new_annotation]))
            self.annotations.save_annotation(new_annotation)
        else:
            self.print_warning(Warnings.NOT_IN_WIKIPEDIA % link)

    def action_print_next(self):
        self.next_entity = self.corpus.next()
        text = self.next_entity.text()
        entity_class = self.next_entity.entity_class()
        print("\n%s[%s] (%s)%s\n" % (ANSI.BOLD, text, entity_class, ANSI.END))
        for entity in self.next_entity:
            corpus_file = self.corpus.files.get(entity.file_name)
            left, right = corpus_file.get_context(entity)
            left = (CONTEXT_SIZE-len(left)) * ' ' + left
            print('    %s[%s%s%s]%s' % (left, ANSI.BLUE, text, ANSI.END, right))
        self.link_suggestion = self.suggest_link(text)
        if self.link_suggestion:
            print('\nLink suggestion: %s' % self.link_suggestion)

    def action_print_annotations(self, search_term=None):
        if search_term is None:
            print("\nCurrent annotations:\n")
            for annotation in self.annotations:
                print(annotation.as_pretty_line())
        else:
            print("\nAnnotations matching '%s':\n" % search_term)
            for annotation in self.annotations:
                if search_term.lower() in annotation.text.lower():
                    print(annotation.as_pretty_line())

    @staticmethod
    def action_set_context(context_size: str):
        global CONTEXT_SIZE
        try:
            n = int(context_size)
            CONTEXT_SIZE = n
        except ValueError:
            print('\nWARNING: context size has to be an integer, ignoring command')

    @staticmethod
    def validate_link(link: str):
        """A link entered by the user is okay if it is either '-' or it is
        longer than one character (to avoid hasty typos) and it occurs in
        Wikipedia."""
        if link == '-':
            return True
        url = 'https://en.wikipedia.org/wiki/%s' % link
        return True if requests.get(url).status_code == 200 else False

    def suggest_link(self, entity_text: str):
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

    def status(self):
        print("\nStatus on %s\n" % self.corpus.annotations_folder)
        # for file_entities in self.corpus_entities:
        for corpus_file in self.corpus.get_files():
            (percent_done_types, percent_done_tokens) = corpus_file.status()
            print('    %s %4d %3d%%' % (corpus_file.name,
                                        corpus_file.entity_type_count(),
                                        percent_done_types))

    def debug_loop(self, message):
        if DEBUG:
            print("\n%s" % message)
            print("    self.action           =  %s" % self.action)
            print("    self.link_suggestion  =  %s" % self.link_suggestion)
            print("    self.next_entity      =  %s" % self.next_entity)

    @staticmethod
    def print_help():
        with open('help.txt') as fh:
            print("\n%s" % fh.read().strip())

    @staticmethod
    def print_warning(message: str):
        print('\n%sWARNING: %s%s' % (ANSI.RED, message, ANSI.END))


def timestamp():
    """Return a timestamp in "YYYY-MM-DD hh:mm:ss" format."""
    dt = datetime.datetime.now()
    return "%04d-%02d-%02d %02d:%02d:%02d" % (dt.year, dt.month, dt.day,
                                              dt.hour, dt.minute, dt.second)


class ANSI(object):
    """ANSI control sequences."""
    BOLD = '\u001b[1m'
    END = '\u001b[0m'
    BLUE = '\u001b[34m'
    RED = '\u001b[31m'


if __name__ == '__main__':

    args = sys.argv[1:]
    if '--debug' in args:
        DEBUG = True
    if '--demo' in args:
        DEMO = True
    Annotator(Corpus(ENTITIES, SOURCES), ANNOTATIONS).loop()
