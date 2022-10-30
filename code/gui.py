"""Simple GUI for Entity Linking

To run this in debug and demo mode:

$ streamlit run gui.py demo debug

Do not use --demo and --debug because then linux and streamlit think those
arguments are streamlit arguments.

"""

import sys
import streamlit as st

import config
import utils
import model

if 'debug' in sys.argv[1:]:
    config.DEBUG = True
if 'demo' in sys.argv[1:]:
    config.DEMO = True
if 'docker' in sys.argv[1:]:
    config.SOURCES = '/data/wgbh-collaboration/21'
    config.ENTITIES = '/data/clams-aapb-annotations/uploads/2022-jun-namedentity/annotations'
    config.ANNOTATIONS = '/data/annotations.tab'
    config.ANNOTATIONS_BACKUP = '/data/annotations-%s.tab'

utils.Messages.debug('(module) %s' % ('-' * 80))
utils.Messages.debug('(module) starting page at %s' % utils.timestamp())

corpus = model.Corpus(config.ENTITIES, config.SOURCES)
link_annotations = model.LinkAnnotations(corpus, config.ANNOTATIONS)

st.set_page_config(layout="wide")
st.markdown(utils.style, unsafe_allow_html=True)
st.markdown("# Entity Link Annotator")

# Using a warning instead of the somewhat easier to use text_input, because
# text_input comes with horrible spacing, so going through the effort to
# maintain message-related variables in an imported module. This may not be
# the best way to do this.
st.warning(utils.Messages.message)


def backup():
    utils.Messages.reset()
    try:
        file_name = link_annotations.backup()
        utils.Messages.info('Backup created in %s' % file_name)
    except OSError:
        utils.Messages.error('Backup failed')


def add_link(link: str = None):
    utils.Messages.reset()
    provided_link = st.session_state.entity_type if link is None else link
    provided_link = link_annotations.normalize_link(provided_link)
    utils.Messages.debug('(add_link)  %s -> %s' % (entity.text(), provided_link))
    if utils.validate_link(provided_link):
        entity.link = provided_link
        link_annotations.add_link(entity, provided_link)
        utils.Messages.info("Linked **%s** to %s" % (entity.text(), provided_link))
        # reset the type only if you are successful
        st.session_state.entity_type = ''
    else:
        utils.Messages.error(config.Warnings.NON_EXISTING_URL % provided_link)


def fix_link(entity_to_fix):
    new_link = st.session_state.entity_type_fix
    new_link = link_annotations.normalize_link(new_link)
    utils.Messages.debug('(fix_link) %s -> %s' % (entity_to_fix, new_link))
    if utils.validate_link(new_link):
        entity_to_fix.link = new_link
        link_annotations.add_link(entity_to_fix, new_link)
        utils.Messages.info("Linked **%s** to %s" % (entity_to_fix.text(), new_link))
    else:
        utils.Messages.error(config.Warnings.NON_EXISTING_URL % new_link)


st.sidebar.button('Backup', on_click=backup)

choice = st.sidebar.radio(
    "Choose", ('Messages', 'Annotations', 'Progress', 'Help', 'State'),
    label_visibility='hidden')

total_types, percentage_done, done_per_file = corpus.status()
st.sidebar.write('Done %d%% of %d types' % (round(percentage_done), total_types))

entity = corpus.next()
utils.Messages.debug('(module) current entity is %s' % entity)
utils.Messages.debug('(module) session_state is %s' % st.session_state)

st.info("**[%s]** (%s)\n" % (entity.text(), entity.entity_class()))
utils.html(st, entity.contexts_as_html(corpus, limit=10))

suggested_link = corpus.suggest_link(entity.text())
st.write('')
if suggested_link is not None:
    utils.Messages.debug('(module) suggested link is %s' % (suggested_link or 'None'))
    st.write('Suggested link: %s' % (suggested_link or None))
    st.button('Accept Suggested Link', on_click=add_link, args=(suggested_link,))

st.text_input("Enter link", key='entity_type', on_change=add_link)

'---'
with st.container():
    # st.write('**%s**' % choice)
    if choice == 'Messages':
        utils.show_messages(st)
    elif choice == 'Annotations':
        utils.show_annotations(st, link_annotations, fix_link)
    elif choice == 'Progress':
        utils.show_progress(st, corpus)
    elif choice == 'Help':
        utils.show_help(st)
    elif choice == 'State':
        utils.show_state(st, sys.modules[__name__])
