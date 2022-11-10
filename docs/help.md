### Using ELA

The ELA tool presents entities from the source corpus one-by-one in a fixed order and for each entity a link can be entered that grounds the entity to an on-line authority. The tool starts with the first document in the corpus, collects all instances of each entity and then presents the first entity to the user with the contexts in which it occurs. It will loop through all the entities in the document and then continue to the next document.

The tool's GUI has three areas:

- A gray pane on the left that includes a backup button, a list of choices on what to display in the auxiliary area and a note that reports progress. By default, the annotations button is selected.
- A top main pane with the next entity to be annotated including contexts and potentially a suggestion on what link to add.
- A auxiliary bottom pane. 

The main pane of this tool shows (i) an optional message printed on a lightyellow background, (ii) the name and category of the next entity to annotate followed by some examples in context an dpotentially a link suggestion, and (iii) a field to enter the link for the entity. Under the main pain is the auxiliary pane with space for one of the following, as determined by the radio buttons in the left pane: 

- a list of messages that were displayed during the current run of the tool
- a list of recent annotations, capped at 25
- a report on annotation progress so far with numbers per document
- help on using the tool (what you are reading now)

When the tool runs in debug mode there will also be a radio button that lets you print the current state of the tool, which is useful for debugging.

**General annotation strategy**

Have two windows open, this tool and [Wikipedia](https://en.wikipedia.org). Look at the entity and its context shown in the main pane. Find a Wikipedia pages that is about the entity described in the context and copy and paste the Wikipedia URL for that entity to the input field (see below) and hit enter. The tool will check whether the URL entered exists (emiting an error message if the link does not exists), print a message that it added a link, add the link to the list of annotations and then present the next entity to be annotated. Any links added will be automatically appended to the end of `data/annotations.tab`.

When the tool encounters an entity that was annotated in a previous document then it will suggest the link from that previous directory and you can just click the button that accompanies the suggestion.

**Using the link input field**

This field is marked with "Enter link and an optional comment" and not surprisingly the primary action for the user is to enter a link. Links can be entered as a full URL. Typically this would be a URL that points at a WIkipedia page, for example [https://en.wikipedia.org/wiki/Jim_Lehrer](https://en.wikipedia.org/wiki/Jim_Lehrer). After entering a URL a simple return sends the URL off to the tool for validation. The tool allows a short hand for the above, where the user can enter just "Jim_Lehrer" and the tool will automatically expand this to the full Wikipedia URL. If no link can be determined then the user can simply enter a space and then hit return.

This field also accepts a comment either in addition to the link or instead of a link. To type in a comment after the link simply type a space followed by three stars (" ***"), all characters entered after the stars will be considered part of the comment. If you only want to add a comment and not ype just start with three stars and then add the comment.

**Viewing past annotations**

The annotaions list in the auxiliary pane shows the last 50 annotations by default. At the end of the list is a "Display entity" input field where you can enter a number from the first column of the annotations list and display that entity. Under the display there is an unlabeled input field with the link, you can use this to fix the link if needed (see below).

You can enter a search term in the "Search annotations" input field to update the display and search older annotations.

**Fixing previous errors**

If you see an error in a past annotation you can fix it. First follow the instructions in "Viewing past annotations" above to select the old annotation. Then just edit the unlabeled field in the same way as you would the edit the "Enter link and an optional comment" field and hit enter. When you do this the old annotation is not removed, all that happens is that a new annotation is added to the top of the list.

**Backing up**

Pressing the "Backup" button creates a time-stamped annotations file in the `data` directory (or another directory if the Docker container was not started in the standard way).

**Known issues and workarounds**

There are some limitations and an error that is not quite solved:

- Sometimes a previously entered link will be added to the next entity. When this happens you will notice a couple of the most recent annotations all having the same link and comment. Use the functionality to fix previous errors as outlined above.
- When accepting a suggested link by clicking the button it is not immediately clear how to add a comment. Do this by enter the comment preceded by three stars in the field marked "Enter link and an optional comment" and then click the button. 
