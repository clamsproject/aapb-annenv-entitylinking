# ELA - Entity Link Annotator

Simple command line annotation tool to add Wikipedia groundings to previously annotated named entities.

Takes as input a set of files with Brat annotations and a set of source files, and creates as output a file `data/annotations.tab` with all entity links.

#### Setting up

The only requirements to run this tool are Python 3.7 or higher and the `requests` module:

```bash
$ pip install requests==2.28.1
```

You also need the source files and entity annotations, which typically, but not neccessarily, are in two GitHub repositories:

- source files: [https://github.com/clamsproject/wgbh-collaboration](https://github.com/clamsproject/wgbh-collaboration) (private repository)
- annotations: [https://github.com/clamsproject/clams-aapb-annotations](https://github.com/clamsproject/clams-aapb-annotations)

The code assumes that both repositories are cloned and uses two variables to store the paths to directories in the cloned repositories:


```python
SOURCES = '../../wgbh-collaboration/21'
ENTITIES = '../../clams-aapb-annotations/uploads/2022-jun-namedentity/annotations/'
```

#### Running the tool

To start the tool do

```bash
$ python main.py
ela>
```

Commands are typed in at the ELA prompt. When you start the tool you get a status report, typing 'n' or hitting return will get you an entity to annotate. To annotate an entry you type`l <link-name>` and the link will be saved after some minimal validation. Just typing `l` stores the empty string as the value of the link, that is, no link was found for the entity.

Entities are annotated in a fixed order and entities cannot be skipped. But you can change the link of a previously annotated entity. For example, if we have an entity `Bill Clinton` and it was accidentally annotated with `Hillary_Clinton`, then you can search for the entity with `a clinton`, look up the identifiers of the relevant entities (we could have spelling variants) and then for each identifier putting in the command `f <n> Bill_Clinton`.

At the tool prompt you can use the following commands:

| command           | description                                                  |
| ----------------- | ------------------------------------------------------------ |
| ? \| h \| help    | print the help message                                       |
| q \| quit \| exit | quit the tool                                                |
| s \| status       | show annotation status                                       |
| n \| &lt;return>   | show next entity to annotate                                 |
| l &lt;link-name>  | store &lt;link-name> as the link for the entity                           |
| y                 | accept the hint that was suggested                           |
| f &lt;n> &lt;link-name> | change link of entity with identifier &lt;n>                                         |
| a                 | show all annotations                                         |
| a &lt;search-term> | show annotations that match the search term                  |
| c &lt;context-size> | set the size of the left and right context in the KWIC, default is 40 |
| b \| backup | create a time-stamped backup in the data directory |
