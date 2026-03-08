"""Pydantic models for states."""

from pathlib import Path
from pydantic import BaseModel, field_validator, ValidationInfo

from b3_state.utils.file_utils import get_file_mtime, is_file_non_empty


class FileState(BaseModel):
    """Model for file state validation."""

    path: Path
    non_empty: bool = True
    newer_than: Path | None = None

    @field_validator("path")
    @classmethod
    def check_exists(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"File does not exist: {v}")
        return v

    @field_validator("non_empty", mode="after")
    @classmethod
    def check_non_empty(cls, v: bool, info: ValidationInfo) -> bool:
        if "path" not in info.data:
            return v
        path = info.data["path"]
        if v and not is_file_non_empty(path):
            raise ValueError(f"File is empty: {path}")
        return v

    @field_validator("newer_than", mode="after")
    @classmethod
    def check_newer_than(cls, v: Path | None, info: ValidationInfo) -> Path | None:
        if v and "path" in info.data:
            path = info.data["path"]
            if get_file_mtime(path) <= get_file_mtime(v):
                raise ValueError(f"File {path} is not newer than {v}")
        return v
