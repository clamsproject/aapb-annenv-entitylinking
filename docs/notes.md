

For wikipedia access maybe use https://pypi.org/project/wikipedia/

```bash
$ pip install wikipedia==1.4.0
```

Use it as follows

```python
>>> import wikipedia as wiki
>>> wiki.page('Jim Lehrer', auto_suggest=False, redirect=False)
>>> wiki.page('Jim_Lehrer', auto_suggest=False, redirect=False)
>>> wiki.page('xJim_Lehrer', auto_suggest=False, redirect=False)
```

For the first two you would get back

```
<WikipediaPage 'Jim Lehrer'>
```

but for the third yiu would get

```
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Applications/ADDED/python/env/clams/linking-annotation-tool/lib/python3.8/site-packages/wikipedia/wikipedia.py", line 276, in page
    return WikipediaPage(title, redirect=redirect, preload=preload)
  File "/Applications/ADDED/python/env/clams/linking-annotation-tool/lib/python3.8/site-packages/wikipedia/wikipedia.py", line 299, in __init__
    self.__load(redirect=redirect, preload=preload)
  File "/Applications/ADDED/python/env/clams/linking-annotation-tool/lib/python3.8/site-packages/wikipedia/wikipedia.py", line 345, in __load
    raise PageError(self.title)
wikipedia.exceptions.PageError: Page id "xJim_Lehrer" does not match any pages. Try another id!
```

