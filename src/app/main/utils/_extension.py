from typing import Any 

from main.pretty import install
from main.tools.traceback import install as tr_install

def load_ipython_extension(ip: Any) -> None:
  install()
  tr_install()