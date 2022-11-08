# ELA Manual - GUI version

These are notes on how to install and start the Graphical User Interface (GUI) version of the ELA tool, for help on using the tool see [help-gui.md](help-gui.md).

The preferred way to run this tool is as a Docker container, but you can also run it without Docker.

### Running the tool with Docker

You need a terminal window and the ability to run Git and Docker:

- Git is needed to get this code and the source data and annotations that are required by this tool, see [https://git-scm.com/book/en/v2/Getting-Started-Installing-Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) on how to install Git.
  - This is optional if all you want to use is one of the released versions and not the most recent version in the main branch of the project (or any version in any branch).
- Docker is a way to package, distribute and run code, see [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/) for help on installation. Make sure that Docker is running when you want to use the ELA tool.

To get the annotation tool code either go to [https://github.com/clamsproject/annotation-entity-linking/releases](https://github.com/clamsproject/annotation-entity-linking/releases) and download the most recent release or type in the following:

```bash
$ git clone https://github.com/clamsproject/annotation-entity-linking
```

You also need the source files and entity annotations, which are in the two GitHub repositories:

- source files: [https://github.com/clamsproject/wgbh-collaboration](https://github.com/clamsproject/wgbh-collaboration) (private repository)
- entity annotations: [https://github.com/clamsproject/clams-aapb-annotations](https://github.com/clamsproject/clams-aapb-annotations)

To run the tool in Docker we need to make sure that the sources, entity annotations and the link annotations that this tool creates all live in the same directory. The easiest way to do this is to put the sources and entities in the `data` directory (which is also where the tool writes all link annotations):

```bash
$ cd annotation-entity-linking/data
$ git clone https://github.com/clamsproject/wgbh-collaboration
$ git clone https://github.com/clamsproject/clams-aapb-annotations
```

The `wgbh-collaboration` is a private repository so you need to have read access to it. When you try to clone it you may be asked for a login and just your account name and password won't do. You will need to create and use a personal access token, see [https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) on how to do that.

Build the Docker image from the top-level of this repository (the level where the Dockerfile is):

```bash
$ cd ..
$ docker build -t link-annotator .
```

The -t option gives a tag to the image, if you do not add a tag the image created will have an obscure name like a146e25431ee, which is fine, but hardly convenient. You do not have to use `link-annotator` as the name, any name will do as long as it meets certain conditions like being all lowercase.

Run the container as follows (this can be from any directory):

```bash
$ docker run -idt --rm -p 8501:8501 -v $PWD/data:/data link-annotator
```

The -v option in the command above creates a directory `/data` on the container and mounts it to the `data` directory in the current directory. Annotations are written to `/data/annotations.tab` on the container and will because of the mount also be available in `data` and therefore persist after the container is stopped and deleted.

To view the application in your browser open [http://localhost:8501](http://localhost:8501). Link annotations will be written to `data/annotations.tab`.

### Running the tool without Docker

The requirements to run this tool without using Docker are:

- A way to get the code: either use Git or download the code from the releases page (see above).
- A recent Python version with the Streamlit module installed. The Streamlit installation documentation [https://docs.streamlit.io/library/get-started/installation](https://docs.streamlit.io/library/get-started/installation) mentions it should run on Python 3.7 thorugh 3.10, but we have had issues running the tool on Python 3.7 and have typically used Python 3.9.

To install Streamlit and its dependencies:

```bash
$ pip install -r code/requirements-gui.txt
```

You can also go for the very latest streamlit and simply do

```bash
$ pip install streamlit
```

On macOS, you may also need to install the Xcode command line tools (see [https://osxdaily.com/2014/02/12/install-command-line-tools-mac-os-x/](https://osxdaily.com/2014/02/12/install-command-line-tools-mac-os-x/).

You also need the source files and entity annotations, which are in the two GitHub repositories mentioned above, install them as follows. The repositories can be installed anywhere and the `code/config.py` script uses two variables, SOURCES and ENTITIES to store the paths to directories in the cloned repositories. You can put the two repositories wherever you want, and they do not have to be in the same directory, but it would probably be easiest to put both repositories in the `data` directory and then set the paths in `code/config.py` as follows:


```python
SOURCES = '../data/wgbh-collaboration/21'
ENTITIES = '../data/clams-aapb-annotations/uploads/2022-jun-namedentity/annotations/'
```

Note that he path is the path from the code directory.

Start the tool from the code directory:

```bash
$ cd code
$ streamlit run gui.py
```

You can then use the application in your browser at [http://localhost:8501](http://localhost:8501). Link annotations will be written to `data/annotations.tab`.

