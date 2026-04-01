from importlib.metadata import version, PackageNotFoundError

try:
    version = version("sequana-denovo")
except PackageNotFoundError:
    version = "unknown"
