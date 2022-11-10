"""Simple GUI for Entity Linking

To run this in production mode and development mode:

$ streamlit run app.py logging
$ streamlit run app.py demo debug logging

Do not use linux command line options like --demo because then linux and
streamlit think those arguments are streamlit arguments.

"""

import sys
import streamlit as st

import config
import utils
import model

st.set_page_config(layout="wide")

utils.Messages.log(('-' * 80))

# Update the configuration given arguments like 'demo' and 'docker'
config.update(sys.argv[1:])

# Load the underlying data from the model and get the next entity
corpus = model.Corpus(config.ENTITIES, config.SOURCES)
link_annotations = model.LinkAnnotations(corpus, config.ANNOTATIONS)
entity = corpus.next()

utils.Messages.log(utils.feature_as_string('current entity', entity))
utils.Messages.log(utils.feature_as_string('session_state', st.session_state))

st.markdown(utils.style, unsafe_allow_html=True)
st.markdown("# Entity Link Annotator")

# Using a warning instead of the somewhat easier to use text_input, because
# text_input comes with horrible spacing, so going through the effort to
# maintain message-related variables in an imported module. This may not be
# the best way to do this.
st.warning(utils.Messages.message)


def backup():
    """Create a time-stamped back up."""
    utils.Messages.reset()
    try:
        file_name = link_annotations.backup()
        utils.Messages.info('Backup created in %s' % file_name)
        utils.Messages.log_info('Backup created in %s' % file_name)
    except OSError:
        utils.Messages.error('Backup failed')
        utils.Messages.log_error('Backup failed')


def add_link(link: str = None):
    """Called when adding a link, the actual link is either taken from the
    entity_type text input or by a suggested link from the code (in which
    case the link argument would be used)."""
    utils.Messages.reset()
    user_input = st.session_state.entity_type if link is None else link
    (link, comment) = utils.split_user_input(user_input)
    link = link_annotations.normalize_link(link)
    utils.Messages.log(utils.feature_as_string('entity', entity))
    validate_and_add(entity, link, comment, post=reset_entity_type)


def fix_link(entity_to_fix):
    """Fix the link and/or the comment on an existing annotation."""
    utils.Messages.log(utils.feature_as_string('session_state', st.session_state))
    (link, comment) = utils.split_user_input(st.session_state.entity_type_fix)
    link = link_annotations.normalize_link(link)
    utils.Messages.log(utils.feature_as_string('entity_to_fix', entity_to_fix))
    validate_and_add(entity_to_fix, link, comment)


def validate_and_add(focus_entity: model.Entity, link: str, comment: str, post=None):
    """Validate the link and add it to the annotations. If a post function is
    given then it will be called, typically to reset some input field."""
    utils.Messages.log(utils.feature_as_string('link', link))
    utils.Messages.log(utils.feature_as_string('session_state', st.session_state))
    utils.Messages.log('Trying [%s] -> [%s] (%s)' % (focus_entity.text(), link, comment))
    if utils.validate_link(link):
        focus_entity.link = link
        focus_entity.comment = comment
        link_annotations.add_link(focus_entity, link, comment)
        utils.Messages.info("Linked **%s** to %s (%s)"
                            % (focus_entity.text(), link, comment))
        utils.Messages.log_info("Linked [%s] to [%s] (%s)"
                                % (focus_entity.text(), link, comment))
        if post is not None:
            post()
    else:
        utils.Messages.error(config.Warnings.NON_EXISTING_URL % link)
        utils.Messages.log_info(config.Warnings.NON_EXISTING_URL % link)


def reset_entity_type():
    utils.Messages.log("old value was '%s'" % st.session_state.entity_type)
    st.session_state.entity_type = ''


st.sidebar.button('Backup', on_click=backup)

# Add the sidebar radio button group with choices
choices = ['Annotations', 'Progress', 'Messages', 'Help']
choices.extend(['State'] if config.DEBUG else [])
choice = st.sidebar.radio(
    "Choose", choices, label_visibility='hidden')

# Add overall progress status to the sidebar
total_types, percentage_done, _ = corpus.status()
st.sidebar.write('Done %d%% of %d types' % (percentage_done, total_types))

# The main area of the window with the entity and its context
st.info("**[%s]** (%s)\n" % (entity.text(), entity.entity_class()))
utils.html(st, entity.contexts_as_html(corpus, limit=10))

# See if the tool suggests a link given past annotations, if so add it to the
# main area accompanied by a button to accept the suggestion
suggested_link = corpus.suggest_link(entity.text())
utils.Messages.log(utils.feature_as_string('suggested link', suggested_link))
st.write('')
if suggested_link is not None:
    st.write('Suggested link: %s' % suggested_link)
    st.button('Accept Suggested Link', on_click=add_link, args=(suggested_link,))

# Input field where the user can add a link and comment
st.text_input('Enter link and an optional comment', key='entity_type', on_change=add_link)

# An auxiliary pane for annotation, messages and status, governed bu the radio
# buttons in the sidebar.
'---'
with st.container():
    if choice == 'Messages':
        utils.DisplayBuilder.show_messages(st)
    elif choice == 'Annotations':
        utils.DisplayBuilder.show_annotations(st, link_annotations, fix_link)
    elif choice == 'Progress':
        utils.DisplayBuilder.show_progress(st, corpus)
    elif choice == 'Help':
        utils.DisplayBuilder.show_help(st)
    elif choice == 'State':
        utils.DisplayBuilder.show_state(st, sys.modules[__name__])
