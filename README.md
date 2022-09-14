# ELA - EntityLinkAnnotator

Simple command line annotation tool to add Wikipedia groundings to previously annotated named entities.

Takes as input a set of files with Brat annotations and the source files, and creates as output a file `data.tab` with all entity links.

The only requirements to run this tool are Python 3.7 or higher and the `requests` module:

```bash
$ pip install requests==2.28.1
```

To start the tool do

```bash
$ python main.py
ela>
```

At the tool prompt you can use the following commands:

| command           | description                                      |
| ----------------- | ------------------------------------------------ |
| ? \| h \| help    | print the help message                           |
| q \| quit \| exit | quit the tool                                    |
| s \| status       | show annotation status                           |
| y                 | accept the hint that was suggested               |
| n \| <return>     | show next entity to annotate                     |
| a                                         | show all annotations                                                                              |
| a <search-term>   | show annotations that match the search term                                            |
| c <context-size>  | set the size of the left and right context in the KWIC, default is 40            |

Commands are typed in at the ELA prompt. If the prompt follows a print out of an entity in context and a non-command is entered then the string that was typed in is considered to be the entity link, if no string was entered and you just hit <return> then the tool will just repeat the entry. Enter  `-` to indicate that there is no corresponding Wikipedia entry for the named entity.
