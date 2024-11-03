from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BaseRecorder:
    def record(self) -> None: ...
