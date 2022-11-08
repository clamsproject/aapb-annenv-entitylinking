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

st.set_page_config(layout="wide")

utils.Messages.debug('(module) %s' % ('-' * 80))
utils.Messages.debug('(module) starting page at %s' % utils.timestamp())

# Update the configuration given arguments like 'demo' and 'docker'
config.update(sys.argv[1:])

# Load the underlying data from the model and get the next entity
corpus = model.Corpus(config.ENTITIES, config.SOURCES)
link_annotations = model.LinkAnnotations(corpus, config.ANNOTATIONS)
entity = corpus.next()

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
    user_input = st.session_state.entity_type if link is None else link
    (link, comment) = utils.split_user_input(user_input)
    link = link_annotations.normalize_link(link)
    validate_and_add('add_link', entity, link, comment, post=reset_entity_type)


def fix_link(entity_to_fix):
    (link, comment) = utils.split_user_input(st.session_state.entity_type_fix)
    link = link_annotations.normalize_link(link)
    validate_and_add('fix_link', entity_to_fix, link, comment)


def validate_and_add(caller: str, focus_entity: model.Entity,
                     link: str, comment: str, post=None):
    """Validate the link and add it to the annotations. If a post function is
    given then it will be called, typically to reset some input field."""
    # TODO: also print the state while debugging
    utils.Messages.debug('(%s)  %s -> %s (%s)'
                         % (caller, entity.text(), link, comment))
    if utils.validate_link(link):
        focus_entity.link = link
        focus_entity.comment = comment
        link_annotations.add_link(focus_entity, link, comment)
        utils.Messages.info("Linked **%s** to %s (%s)"
                            % (focus_entity.text(), link, comment))
        if post is not None:
            post()
    else:
        utils.Messages.error(config.Warnings.NON_EXISTING_URL % link)


def reset_entity_type():
    utils.Messages.debug("Resetting entity type (old value = %s)"
                         % st.session_state.entity_type)
    st.session_state.entity_type = ''


st.sidebar.button('Backup', on_click=backup)

# Add the sidebar radio button group with choices
choices = ['Annotations', 'Progress', 'Messages', 'Help']
if config.DEBUG:
    choices.append('State')
choice = st.sidebar.radio(
    "Choose", choices, label_visibility='hidden')

total_types, percentage_done, done_per_file = corpus.status()
st.sidebar.write('Done %d%% of %d types' % (round(percentage_done), total_types))

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

st.text_input('Enter link and an optional comment', key='entity_type', on_change=add_link)

'---'
with st.container():
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
