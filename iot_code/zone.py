from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np


Point = tuple[int, int]


@dataclass(frozen=True)
class ZoneConfig:
    danger_zone: tuple[Point, ...]
    warning_zone: tuple[Point, ...]


def _as_polygon(points: Iterable[Point]) -> np.ndarray:
    polygon = np.asarray(list(points), dtype=np.int32)
    if polygon.ndim != 2 or polygon.shape[0] < 3 or polygon.shape[1] != 2:
        raise ValueError("A zone must contain at least three (x, y) points")
    return polygon.reshape((-1, 1, 2))


def point_in_polygon(point: Point, polygon: Iterable[Point]) -> bool:
    return cv2.pointPolygonTest(_as_polygon(polygon), point, False) >= 0


def classify_foot_point(point: Point, zones: ZoneConfig) -> str:
    if point_in_polygon(point, zones.danger_zone):
        return "DANGER"
    if point_in_polygon(point, zones.warning_zone):
        return "WARNING"
    return "SAFE"


def draw_zones(frame: np.ndarray, zones: ZoneConfig) -> np.ndarray:
    output = frame.copy()
    cv2.polylines(
        output,
        [_as_polygon(zones.warning_zone)],
        isClosed=True,
        color=(0, 165, 255),
        thickness=2,
    )
    cv2.polylines(
        output,
        [_as_polygon(zones.danger_zone)],
        isClosed=True,
        color=(0, 0, 255),
        thickness=3,
    )
    return output
