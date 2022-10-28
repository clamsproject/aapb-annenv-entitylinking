"""Entity Linking model

This contains all the code for the model underlying the interface. It has
classes to deal with the corpus and files in the corpus, as well as entities
and annotations in those files.

"""

import os
import copy
import shutil
import pathlib
import collections
from io import StringIO

import config
import utils
from utils import timestamp


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
        self._add_dummy_data()

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

    def _add_dummy_data(self):
        """Create a dummy file from an existing file, using only the most common
        entities from the existing file. Then add it to the beginning of the file
        list. This is for demonstrating the tool."""
        def add_entity(dummy_file, source_file, etype):
            dummy_file.source = source_file.source
            dummy_entity = copy.deepcopy(etype)
            dummy_entity.file_name = dummy_file.name
            for token in dummy_entity:
                token.file_name = dummy_file.name
            dummy_file.data[entity_type.text()] = dummy_entity
        if config.DEMO:
            file_names = self.get_file_names()
            dummy1_file_name = 'cpb-aacip-000-0000000001-transcript.ann'
            dummy2_file_name = 'cpb-aacip-000-0000000002-transcript.ann'
            first_file = self.files.get(file_names[0])
            dummy1_file = File(dummy1_file_name)
            dummy2_file = File(dummy2_file_name)
            for entity_text, entity_type in first_file.data.items():
                if not len(entity_type) > 2:
                    continue
                # utils.Messages.debug('>>> (_add_dummy_data) %s' % entity_type)
                if len(entity_type) > 5:
                    add_entity(dummy1_file, first_file, entity_type)
                if len(entity_type) > 2:
                    add_entity(dummy2_file, first_file, entity_type)
            self.files[dummy1_file_name] = dummy1_file
            self.files[dummy2_file_name] = dummy2_file

    def __str__(self):
        return '<Corpus files=%d>' % (len(self.files))

    def get_files(self):
        """Return all File instances in the corpus, sorted on the filename."""
        return [self.files[file_name] for file_name in sorted(self.files)]

    def get_file_names(self) -> list:
        """Return all file names in the corpus."""
        return list(sorted(self.files))

    def get_entity(self, text: str, fname: str):
        """Return the EntityType for the text in file fname."""
        file = self.files.get(fname + '-transcript.ann')
        entity = file.data.get(text)
        return entity

    def data_locations(self):
        return [['SOURCES', self.sources_folder],
                ['ENTITIES', self.annotations_folder]]

    def next(self):
        """Return the first un-annotated entity."""
        for corpus_file in self.get_files():
            for type_entity in corpus_file.data.values():
                if type_entity.link is None:
                    return type_entity

    def suggest_link(self, entity_text: str):
        """Given an entity, suggest a possible link by looking at previously
        annotated entities."""
        suggestions = []
        for corpus_file in self.get_files():
            suggestion = corpus_file.data.get(entity_text)
            if suggestion is not None and suggestion.link is not None:
                suggestions.append(suggestion.link)
        c = collections.Counter(suggestions)
        try:
            return c.most_common()[0][0]
        except IndexError:
            return None

    def status(self):
        corpus_types = 0
        corpus_types_done = 0
        result = []
        for corpus_file in self.get_files():
            (total_types, types_done, percent_done_types) = corpus_file.status()
            corpus_types += total_types
            corpus_types_done += types_done
            result.append([corpus_file.name,
                           corpus_file.entity_type_count(),
                           round(percent_done_types)])
        corpus_percentage_done = (corpus_types_done / corpus_types) * 100
        return corpus_types, corpus_percentage_done, result


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
        left = normalize(self.source[p1 - config.CONTEXT_SIZE:p1])
        right = normalize(self.source[p2:p2 + config.CONTEXT_SIZE])
        return left, right

    def status(self) -> tuple:
        """Return the total number of entity types, the number of entity types
        done and the percentage done for entity types."""
        done_types = 0
        done_tokens = 0
        for entity_type in self.data.values():
            if entity_type.link is not None:
                done_types += 1
                done_tokens += len(entity_type)
        percent_done_types = (done_types * 100 / self.entity_type_count())
        return self.entity_type_count(), done_types, percent_done_types

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

    def contexts(self, corpus, limit=9999):
        """Return all contexts for this entity as a list of <left, text, right> tuples."""
        contexts = []
        for entity in self[:limit]:
            corpus_file = corpus.files.get(entity.file_name)
            left, right = corpus_file.get_context(entity)
            left = (config.CONTEXT_SIZE - len(left)) * ' ' + left
            contexts.append([left, self.text(), right])
        return contexts

    def contexts_as_html(self, corpus, limit=9999):
        """Return all contexts of the entity as an HTML table."""
        s = StringIO('<table>\n')
        for left, kw, right in self.contexts(corpus, limit=limit):
            s.write('<tr>\n')
            s.write('  <td align="right">%s</td>\n' % left)
            s.write('  <td><font color="blue">%s</font></td>' % kw)
            s.write('  <td>%s</td>' % right)
            s.write('<tr>\n')
        s.write('</table>\n')
        return s. getvalue()

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
        fields = line.strip('\n').strip(' ').split('\t')
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

    def is_dummy_annotation(self) -> bool:
        """Returns True if this file was created as a dummy for the demo mode."""
        return '000-0000000000' in self.file_name

    def fields(self) -> tuple:
        """Returns the values of all instance variables in a fixed order."""
        return (self.identifier, self.timestamp, self.file_name, self.text,
                self.entity_class, self.tokens, self.link)

    def as_pretty_line(self) -> str:
        """Returns a line for pretty printing in the tool."""
        identifier = self.identifier
        fname = "%s:%s" % (self.file_name[:-15], self.tokens)
        e_class, e_text, link = self.entity_class, self.text, self.link
        return ("%4s %-30s %-17s  -  %-33s  ==>  %s"
                % (identifier, fname, e_class, e_text, link))

    def as_tab_separated_line(self) -> str:
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

    def __str__(self):
        return '<LinkAnnotations annotations=%s>' % len(self.annotations)

    def __getitem__(self, item):
        return self.annotations[item]

    @classmethod
    def is_link(cls, link: str) -> bool:
        """Return True if the link string starts with 'http://' or 'https://',
        return False otherwise."""
        for prefix in config.URL_PREFIXES:
            if link.startswith(prefix):
                return True
        return False

    @classmethod
    def normalize_link(cls, link: str) -> str:
        """Replace spaces with underscores and expand to a full Wikipedia URL
        if needed. If no link was given then return the emtpy string."""
        link = link.strip().replace(' ', '_')
        if not link:
            return ''
        return link if cls.is_link(link) else config.WIKIPEDIA_LINK % link

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
        if not config.DEMO and annotation.is_dummy_annotation():
            return
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

    def create_link(self, link, entity=None, annotation=None) -> list:
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

    def backup(self) -> str:
        source_file = self.annotations_file
        target_file = config.ANNOTATIONS_BACKUP % timestamp().replace(' ', ':')
        shutil.copyfile(source_file, target_file)
        return target_file

    def search(self, search_term: str):
        """Returns a list of all the annotations where the search term occurs
        in the text. The search us case-insensitive."""
        result = []
        for annotation in self:
            if search_term.lower() in annotation.text.lower():
                result.append(annotation)
        return result
