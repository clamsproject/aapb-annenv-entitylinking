# The ELA GUI



## Installation

```bash
$ python3 -m venv /Applications/ADDED/python/env/clams/ann-nel-gui
$ ln -s /Applications/ADDED/python/env/clams/ann-nel-gui/bin/activate venv-gui
$ source venv-gui
$ python -m pip install --upgrade pip
$ pip install streamlit
$ pip freeze > requirements-gui.txt
```

The streamlit install will also install the requests module which was the only dependency of the command line tool. Note that the exact version of requests is the same here, but one of the modules installed with requests has a different version (see the two requirements files).

### Issues

I did this first with Python 3.8.9. I noticed that I could not run streamlit on the iMac at work which has Python 3.7. Allegedly you need Python 3.9 or higher. So I installed Python 10 at work. However, I could not run

```bash
$ pip install -r requirements-gui.txt
```

So I fell back to

```bash
$ pip install streamlit
```

The pip freeze from that differs from the requirements file:

```bash
$ pip freeze > requirements-gui-3.10.txt
$ diff requirements-gui-3.10.txt requirements-gui.txt
```

```diff
2a3
> backports.zoneinfo==0.2.1
14a16
> importlib-resources==5.10.0
21a24
> pkgutil_resolve_name==1.3.10
46c49
< zipp==3.10.0
---
> zipp==3.9.0
```

