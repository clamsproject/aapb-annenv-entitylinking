"""Configuration settings

Contains variables with the run-time configuration settings.

"""

DEBUG = False
DEMO = False
ANNOTATIONS = 'data/annotations.tab'
ANNOTATIONS_BACKUP = 'data/annotations-%s.tab'
CONTEXT_SIZE = 50
PROMPT = 'ela>'
URL_PREFIXES = ('http://', 'https://')
WIKIPEDIA_LINK = 'https://en.wikipedia.org/wiki/%s'


class Warnings(object):
    NO_ENTITY = 'No entity was selected, type "n" to select next entity'
    UNKNOWN_COMMAND = 'Unknown command, type "h" to see available commands'
    NO_LINK_SUGGESTION = 'There was no link suggestion'
    NON_EXISTING_URL = "The URL %s does not exist"
