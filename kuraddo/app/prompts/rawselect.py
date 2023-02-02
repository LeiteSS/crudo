from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Union

from prompt_toolkit.styles import Style

from main.constants.constants import DEFAULT_QUESTION_PREFIX
from main.constants.constants import DEFAULT_SELECTED_POINTER
from main.prompts import select
from main.prompts.common import Choice
from main.model.question import Question

def rawselect(
  message: str,
  choices: Sequence[Union[str, Choice, Dict[str, Any]]],
  default: Optional[str] = None,
  qmark: str = DEFAULT_QUESTION_PREFIX,
  pointer: Optional[str] = DEFAULT_SELECTED_POINTER,
  style: Optional[Style] = None,
  **kwargs: Any,
) -> Question:
  """Ask the user to select one item from a list of choices using shortcuts.
  
  The use can only select one option.

  Args:
      message: Question text.

      choices: Items shown in the selection, this can contain :class:`Choice` or
               :class:`Separator` objects or simple items as strings. Passing
               :class:`Choice` objects, allows you to configure the item more
               (e.g. preselecting it or disabling it).

      default: Default return value (single value).

      qmark: Question prefix displayed in front of the question.
             By default this is a ``?``.

      pointer: Pointer symbol in front of the currently highlighted element.
               By default this is a ``>>``.
               Use ``None`` to disable it.

      style: A custom color and style for the question parts. You can
             configure colors as well as font types for different elements.

  Returns:
      :class:`Question`: Question instance, ready to be prompted (using ``.ask()``).  
  """
  return select.select(
    message,
    choices,
    default,
    qmark,
    pointer,
    style,
    use_shortcuts=True,
    use_arrow_keys=False,
    **kwargs,
  )