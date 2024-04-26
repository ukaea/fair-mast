import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class UploadConfig:
    url: str
    endpoint_url: str
    credentials_file: str
