"""Configuration settings

Contains variables with the run-time configuration settings.

"""

DEBUG = False
DEMO = False
LOGGING = False

# Locations of the source and entity annotation repositories, edit as needed
SOURCES = '../../../wgbh-collaboration/21'
ENTITIES = '../../../clams-aapb-annotations/uploads/2022-jun-namedentity/annotations'

ANNOTATIONS = '../data/annotations.tab'
ANNOTATIONS_BACKUP = '../data/annotations-%s.tab'
LOGGING_FILE = '../data/log.tab'

# Settings for the number of characters in the left and right context, the
# maximum number of context elements to print for an entity, and the maximum
# number of annotations to print
CONTEXT_SIZE = 50
MAX_CONTEXT_ELEMENTS = 10
MAX_ANNOTATIONS_DISPLAYED = 25

PROMPT = 'ela>'
URL_PREFIXES = ('http://', 'https://')
WIKIPEDIA_LINK = 'https://en.wikipedia.org/wiki/%s'

# Locations are all fixed to the /data directory when using Docker
_DOCKER_SETTINGS = {
    'SOURCES': '/data/wgbh-collaboration/21',
    'ENTITIES': '/data/clams-aapb-annotations/uploads/2022-jun-namedentity/annotations',
    'ANNOTATIONS': '/data/annotations.tab',
    'ANNOTATIONS_BACKUP': '/data/annotations-%s.tab',
    'LOGGING_FILE': '/data/log.tab' }


class Warnings(object):
    NO_ENTITY = 'No entity was selected, type "n" to select next entity'
    UNKNOWN_COMMAND = 'Unknown command, type "h" to see available commands'
    NO_LINK_SUGGESTION = 'There was no link suggestion'
    NON_EXISTING_URL = "The URL %s does not exist"


def update(args):
    """Updates the configuration settings given arguments handed in at startup
    time, arguments include 'demo', 'debug' and 'docker'."""
    global DEBUG, DEMO, LOGGING
    global SOURCES, ENTITIES, ANNOTATIONS, ANNOTATIONS_BACKUP, LOGGING_FILE
    DEBUG = True if 'debug' in args else False
    DEMO = True if 'demo' in args else False
    LOGGING = True if 'logging' in args else False
    if 'docker' in args:
        SOURCES = _DOCKER_SETTINGS['SOURCES']
        ENTITIES = _DOCKER_SETTINGS['ENTITIES']
        ANNOTATIONS = _DOCKER_SETTINGS['ANNOTATIONS']
        ANNOTATIONS_BACKUP = _DOCKER_SETTINGS['ANNOTATIONS_BACKUP']
        LOGGING_FILE = _DOCKER_SETTINGS['LOGGING_FILE']
