from pathlib import Path

cache_dir = Path("cache")
data_dir = Path("data")
js_dir = Path("js")
cache_dir.mkdir(exist_ok=True)
data_dir.mkdir(exist_ok=True)
js_dir.mkdir(exist_ok=True)
