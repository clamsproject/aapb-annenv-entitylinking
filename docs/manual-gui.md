# ELA Manual - GUI version

Notes on how to use the Graphical User Interface (GUI) version of the ELA tool.

#### Setting up

The requirements to run this tool are a recent Python version with Streamlit installed. The Streamlit installation documentation [https://docs.streamlit.io/library/get-started/installation](https://docs.streamlit.io/library/get-started/installation) mentions it should run on Python 3.7-3.10, but we have had issues running the tool on Python 3.7 and have used Python 3.9 or 3.10.  To install Streamlit:

```bash
$ pip install streamlit
```

Alternatively you use the `code/requirements-gui.txt` file which lists all the dependencies with version numbers.

On macOS, you may need to install the Xcode command line tools (see [https://osxdaily.com/2014/02/12/install-command-line-tools-mac-os-x/](https://osxdaily.com/2014/02/12/install-command-line-tools-mac-os-x/).

You also need the source files and entity annotations, which at the moment are in two GitHub repositories:

- source files: [https://github.com/clamsproject/wgbh-collaboration](https://github.com/clamsproject/wgbh-collaboration) (private repository)
- annotations: [https://github.com/clamsproject/clams-aapb-annotations](https://github.com/clamsproject/clams-aapb-annotations)

The code assumes that both repositories are cloned in the same directory and the `code/config.py` script uses two variables to store the paths to directories in the cloned repositories:


```python
SOURCES = '../../../wgbh-collaboration/21'
ENTITIES = '../../../clams-aapb-annotations/uploads/2022-jun-namedentity/annotations/'
```

Edit these as needed.

#### Running the tool

Start the tool from the code directory:

```bash
$ cd code
$ streamlit run gui.py
```

You can then use the application in your browser at [http://localhost:8501](http://localhost:8501).

Link annotations will be written to `data/annotations.tab`.

### Using Docker

To start the tool we need to make sure that the sources, entities and link annotations live in the same directory. The easiest way to do this is to put them all in the `data` directory:

```bash
$ cd data
$ git clone https://github.com/clamsproject/wgbh-collaboration
$ git clone https://github.com/clamsproject/clams-aapb-annotations
```

Build the Docker image from the top-level of this repository (the level where the Dockerfile is):

```bash
$ docker build -t IMAGE_NAME .
```

Run the container from the same directory as follows:

```bash
$ docker run -idt --rm -p 8501:8501 -v $PWD/data:/data IMAGE_NAME
```

The -v option in the command above creates a directory `/data` on the container and mounts it to the `data` directory in the current directory. Annotations are written to `/data/annotations.tab` on the container and will because of the mount also be available in `data` and therefore persist after the container is stopped and deleted.

To view the application in your browser open [http://localhost:8501](http://localhost:8501).
