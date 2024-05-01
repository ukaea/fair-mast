from dataclasses import dataclass


@dataclass
class UploadConfig:
    url: str
    endpoint_url: str
    credentials_file: str
