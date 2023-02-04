from math import sqrt
from functools import lru_cache
from typing import Sequence, Tuple, TYPE_CHECKING

from .color_triplet import ColorTriplet

if TYPE_CHECKING:
  from app.table import Table

