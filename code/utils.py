import datetime
import inspect

import requests
import pandas as pd

import config


def timestamp():
    """Return a timestamp in "YYYY-MM-DD hh:mm:ss" format."""
    dt = datetime.datetime.now()
    return "%04d-%02d-%02d %02d:%02d:%02d" % (dt.year, dt.month, dt.day,
                                              dt.hour, dt.minute, dt.second)


class Messages:

    message = '*Messages go here*'
    messages = [(timestamp(), 'INFO', 'Started Entity Link Annotator')]

    @classmethod
    def reset(cls):
        cls.message = '*Messages go here*'

    @classmethod
    def info(cls, message_text: str):
        cls.messages.insert(0, (timestamp(), 'INFO', message_text))
        cls.message = 'INFO: %s' % message_text

    @classmethod
    def error(cls, error_text: str):
        cls.messages.insert(0, (timestamp(), 'ERROR', error_text))
        cls.message = '**ERROR**: %s' % error_text

    @classmethod
    def debug(cls, text: str):
        if config.DEBUG:
            print('>>> %s' % text)

    @classmethod
    def log(cls, text: str, source=None, entry_type='DEBUG'):
        if config.LOGGING:
            frame: inspect.FrameInfo = inspect.stack()[1]
            source = frame.function if source is None else source
            with open(config.LOGGING_FILE, 'a') as fh:
                source = source if source.startswith('<') else '(%s)' % source
                fh.write(f'{timestamp()} : {entry_type:5s} : {source:20s}  --  {text}\n')

    @classmethod
    def log_info(cls, text: str, source=None):
        source = inspect.stack()[1].function if source is None else source
        cls.log(text, entry_type='INFO', source=source)

    @classmethod
    def log_error(cls, text: str, source=None):
        source = inspect.stack()[1].function if source is None else source
        cls.log(text, entry_type='ERROR', source=source)


def feature_as_string(feature_name: str, feature_value: object):
    return f'{feature_name:15s}  =  {feature_value}'


def split_user_input(user_input: str) -> tuple:
    user_input = user_input.strip()
    if not user_input.strip():
        return '', ''
    if user_input.startswith('***'):
        return '', user_input[3:]
    link, *comment = user_input.split(' ***', 1)
    return link.strip(), comment[0].strip() if comment else ''


def all_vars(module, session_state):
    """Return tuples for all interesting state variables with variable type,
    variable name and variable value."""
    return (
        [('config', v, val) for v, val in _config_vars()]
        + [('session_state', var, val) for var, val in session_state.items()]
        + [('module', v, val) for v, val in _module_vars(module)])


def _module_vars(module):
    return (module.corpus.data_locations()
            + [['corpus', str(module.corpus)], ['annotations', module.link_annotations],
               ['entity', module.entity], ['suggested_link', module.suggested_link]])


def _config_vars():
    return [(v, getattr(config, v)) for v in dir(config)
            if not v.startswith('_') and v not in ('Warnings', 'update')]


def validate_link(link: str):
    """A link entered by the user is okay if it is either an empty link or
    it exists as a URL."""
    if not link:
        return True
    return True if requests.get(link).status_code == 200 else False


def html(streamlit, text: str):
    """Writes a texts as html using streamlit."""
    streamlit.markdown(text, unsafe_allow_html=True)


class DisplayBuilder(object):

    """Utility class to build elements of the auxiliary pane in the tool."""

    @classmethod
    def show_progress(cls, streamlit, corpus):
        total_types, percentage_done, done_per_file = corpus.status()
        # streamlit.write('Done %d%% of %d types' % (round(percentage_done), total_types))
        streamlit.table(pd.DataFrame(done_per_file, columns=['file', 'entities', '% done']))

    @classmethod
    def show_messages(cls, streamlit):
        streamlit.table(pd.DataFrame(Messages.messages,
                                     columns=['timestamp', 'type', 'message']))

    @classmethod
    def show_state(cls, streamlit, module):
        streamlit.table(
            pd.DataFrame(
                all_vars(module, streamlit.session_state),
                columns=['type', 'variable', 'value']))

    @classmethod
    def show_help(cls, st):
        with open('../docs/help.md') as fh:
            st.markdown(fh.read())

    @classmethod
    def show_annotations(cls, streamlit, annotations, callback=None):
        streamlit.text_input('Search annotations', key='search')
        annos = list(reversed(annotations.search(streamlit.session_state.search)))
        annos = annos[:config.MAX_ANNOTATIONS_DISPLAYED]
        table = annotations_as_table(annos)
        streamlit.table(
            pd.DataFrame(table, columns=['id', 'file', 'n', 'text', 'type', 'link', 'comment']))
        streamlit.text_input('Display entity', key='display')
        if streamlit.session_state.display:
            DisplayBuilder.show_entity(streamlit, table, annotations, callback)

    @classmethod
    def show_entity(cls, streamlit, table, annotations, callback):
        try:
            idx = int(streamlit.session_state.display)
            row = select_row(table, idx)
            if row is None:
                streamlit.error('There is no row with id=%s' % idx)
            else:
                _id, fname, _n, etext, _etype, link, comment = row
                entity = annotations.corpus.get_entity(etext, fname)
                streamlit.info("**[%s]** (%s) &longrightarrow; %s\n"
                               % (entity.text(), entity.entity_class(), link))
                html(streamlit,
                     entity.contexts_as_html(annotations.corpus,
                                             limit=config.MAX_CONTEXT_ELEMENTS))
                link_and_comment = '%s *** %s' % (link, comment) if comment else link
                streamlit.text_input("Fix link", key='entity_type_fix',
                                     on_change=callback, args=(entity,),
                                     value=link_and_comment, label_visibility='hidden')
        except ValueError:
            streamlit.error('Please enter a numer from the first column above')


def annotations_as_table(annotations):
    table = []
    for annotation in annotations:
        ident, ts, fname, text, cat, count, link, comment = annotation.fields()
        if fname.endswith('-transcript.ann'):
            fname = fname[:-15]
        table.append([ident, fname, count, text, cat, link, comment])
    return table


def select_row(table: list, term, column=0):
    for row in table:
        if row[column] == term:
            return row
    return None


style = """
<style>
thead tr th:first-child {display:none}
tbody th {display:none}
</style>
"""


class ANSI(object):
    """ANSI control sequences."""
    BOLD = '\u001b[1m'
    END = '\u001b[0m'
    BLUE = '\u001b[34m'
    RED = '\u001b[31m'
