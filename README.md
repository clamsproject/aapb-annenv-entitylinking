# ELA - Entity Link Annotator

This annotator takes as input a set of files with Brat annotations and a set of source files, and creates an output file `data/annotations.tab` with entity links. It is geared towards defining Wikipedia links for named entities in an annotation.

There are two versions of this tool: a command line version and a GUI version, which both interact with the same underlying data. These versions have different installation procedures and obviously work differently, see the documentation in [docs/manual-repl.md](docs/manual-repl.md) and  [docs/manual-gui.md](docs/manual-gui.md).
