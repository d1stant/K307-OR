from pathlib import Path

cache_dir = Path("cache")
data_dir = Path("data")
cache_dir.mkdir(exist_ok=True)
data_dir.mkdir(exist_ok=True)
