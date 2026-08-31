# Improve Jekyll Asset Location Logic

I improved the Python script that prepares `site-src` to include the top-level obsidian vault directory for images. This allows us to later navigate to those locations to showcase the assets we have, if desired

For example, this vault image:
```python
|-- absurdly-goud-obsidian/
        |-- 88x31/
            |-- memes-as-buttons/
                |-- free-real-estate.svg
```

Will be copied into a directory `site_src`:
```python
|-- site_src/
	|-- assets/
		|-- 88x31/
			|-- free-real-estate.svg
```

The removal of the middle directories are intentional, as seen with posts:
```python
|-- absurdly-goud-obsidian/
        |-- 88x31/
            |-- memes-as-buttons/
                |-- free-real-estate.svg
        ...
        |-- posts/
            |-- 2026/
                |-- 08/
                    |-- 24/
                        ...
                        |-- 2026-08-24-aside-and-buttons-screenshot.png
```
is copied into:
```python
|-- site_src/
	|-- assets/
		|-- posts/
			|-- 2026-08-24-aside-and-buttons-screenshot.png
```
