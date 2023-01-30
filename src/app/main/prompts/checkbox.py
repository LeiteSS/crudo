from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from prompt_toolkit.styles import merge_styles

from main.utils import utils
from main.constants.constants import DEFAULT_QUESTION_PREFIX
from main.constants.constants import DEFAULT_SELECTED_POINTER
from main.constants.constants import DEFAULT_STYLE
from main.constants.constants import INVALID_INPUT
from main.prompts import common
from main.prompts.common import Choice
from main.prompts.common import InquirerControl
from main.prompts.common import Separator
from main.model.question import Question

def checkbox(
  message: str,
  choices: Sequence[Union[str, Choice, Dict[str, Any]]],
  default: Optional[str] = None,
  validate: Callable[[List[str]], Union[bool, str]] = lambda a: True,
  qmark: str = DEFAULT_QUESTION_PREFIX,
  pointer: Optional[str] = DEFAULT_SELECTED_POINTER,
  style: Optional[Style] = None,
  initial_choice: Optional[Union[str, Choice, Dict[str, Any]]] = None,
  use_arrow_keys: bool = True,
  use_ws_keys: bool = True,
  use_emacs_keys: bool = True,
  **kwargs: Any,
) -> Question:
  """Ask the user to select from a list of items.
  
  This is a multiselect, the user can choose one, none or many of the
  items.

  Args: 
      message: Question text

      choices: Items shown in the selection, this can contain :class:`Choice`or
               or :class:`Separator`objects or simple items as strings. Passing
               :class:`Choice` objects, allows you to configure the item more
               (e.g. preselecting it or disabling it).
      
      default: Default return value (single value). If you want to preselect
               multiple items, use ``Choice("foo", checked=True)`` instead.
      
      validate: Require the entered value to pass a validation. The
                value can not be submitted util the validator accepts
                it (e.g. to check minimum password length).

                This should be a function accepting the input and
                returning a boolean. Alternatively, the return value
                may be a string (indicating failure), which contains
                the error message to be displayed.
      
      qmark: Question prefix displayed in front of the question.
             By default this is a ``?``.

      pointer: Pointer symbol in front of the currently higlighted element.
               By default this is a ``>>``.
               Use ``None`` to disable it.
      
      style: A custom color and style for the question parts. You can
             configure colors as well as font types for different elements.

      initial_choice: A value corresponding to a selectable item in the choices,
                      to initially set the pointer position to.
      
      use_arrow_keys: Allow the user to select items from the list using
                      arrow keys.
      
      use_ws_keys: Allow user to select items from the list using `
                   `s` (down) and `w` (up) keys like a true gamer.

      use_emacs_keys: Allow the user to select items from the list using
                      `Ctrl+N` (down) and `Ctrl+P` (up) keys.
      
    Returns:
        :class:`Question`: Question instance, ready to be prompted (using ``.ask()``).
  """

  if not (use_arrow_keys or use_ws_keys or use_emacs_keys):
    raise ValueError(
      "Some option to move the selection is required. Arrow keys or w/s or "
      "Emacs keys."
    )
  
  merged_style = merge_styles(
    [
      DEFAULT_STYLE,
      #Disable the default inverted colours bottom-toolbar behaviour (for
      # the error message). However it can be re-enabled with a custom
      # style.
      Style(["bottom-toolbar", "noreverse"]),
      style,
    ]
  )

  if not callable(validate):
    raise ValueError("validate must be callable")
  
  inquirerControl = InquirerControl(
    choices, 
    default, 
    pointer=pointer, 
    initial_choice=initial_choice
  )

  def get_prompt_tokens() -> List[Tuple[str, str]]:
    tokens = []

    tokens.append(("class:qmark", qmark))
    tokens.append(("class:question", " {} ".format(message)))

    if inquirerControl.is_answered:
      nbr_selected = len(inquirerControl.selected_options)

      if nbr_selected == 0:
        tokens.append(("class:answer", "done"))
      elif nbr_selected == 1:
        if isinstance(inquirerControl.get_selected_values()[0].title, list):
          tokenSelected = inquirerControl.get_selected_values()[0].title
          tokens.append(
            (
              "class:answer",
              "".join([token[1] for token in tokenSelected]), # type: ignore
            )
          )
        else:
          tokens.append(
            (
              "class:answer",
              "[{}]".format(inquirerControl.get_selected_values()[0].title),
            )
          )
      else:
        tokens.append(
          ("class:answer", "done ({} selections)".format(nbr_selected))
        )
    else:
      tokens.append(
        (
          "class:instruction",
          "(Use arrow key to move, "
          "<space> to select, "
          "<a>  to toggle, "
          "<i> to invert)",
        )
      )
    
    return tokens
  
  def get_selected_values() -> List[Any]:
    return [selectedValue.value for selectedValue in inquirerControl.get_selected_values()]
  
  def perform_validation(selected_values: List[str]) -> bool:
    verdict = validate(selected_values)
    valid = verdict is True

    if not valid:
      if verdict is False:
        error_text = INVALID_INPUT
      else:
        error_text = str(verdict)
      
      error_message = FormattedText(["class:validation-toolbar", error_text])
    
    inquirerControl.error_message = (
      error_message if not valid and inquirerControl.submission_attempted else None
    )

    return valid

  layout = common.create_inquirer_layout(inquirerControl, get_prompt_tokens, **kwargs)

  bindings = KeyBindings()

  @bindings.add(Keys.ControlQ, eager=True)
  @bindings.add(Keys.ControlC, eager=True)
  def _(event):
    event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

  @bindings.add(" ", eager=True)
  def toggle(_event):
    pointed_choice = inquirerControl.get_pointed_at().value

    if pointed_choice in inquirerControl.selected_options:
      inquirerControl.selected_options.remove(pointed_choice)
    else:
      inquirerControl.selected_options.append(pointed_choice)
    
    perform_validation(get_selected_values())

  @bindings.add("i", eager=True)
  def invert(_event):
    inverted_selection = [
      choice.value
      for choice in inquirerControl.choices
      if not isinstance(choice, Separator)
      and choice.value not in inquirerControl.selected_options
      and not choice.disabled
    ]
    inquirerControl.selected_options = inverted_selection

    perform_validation(get_selected_values())
  
  @bindings.add("a", eager=True)
  def all(_event):
    all_selected = True # all choices have been selected

    for choice in inquirerControl.choices:
      if (
        not isinstance(choice, Separator)
        and choice.value not in inquirerControl.selected_options
        and not choice.disabled
      ):
        # add missing ones
        inquirerControl.selected_options.append(choice.value)
        all_selected = False
    
    if all_selected:
      inquirerControl.selected_options = []
    
    perform_validation(get_selected_values())

  def move_cursor_down(event):
    inquirerControl.select_next()
    while not inquirerControl.is_selection_valid():
      inquirerControl.select_next()
  
  def move_cursor_up(event):
    inquirerControl.select_previous()
    while not inquirerControl.is_selection_valid():
      inquirerControl.select_previous()
  
  if use_arrow_keys:
    bindings.add(Keys.Down, eager=True)(move_cursor_down)
    bindings.add(Keys.Up, eager=True)(move_cursor_up)
  
  if use_ws_keys:
    bindings.add("s", eager=True)(move_cursor_down)
    bindings.add("w", eager=True)(move_cursor_up)
  
  if use_emacs_keys:
    bindings.add(Keys.ControlN, eager=True)(move_cursor_down)
    bindings.add(Keys.ControlP, eager=True)(move_cursor_up)
  
  # Keys.ControlM
  @bindings.add(Keys.ControlX, eager=True)
  def set_answer(event):
    selected_values = get_selected_values()
    inquirerControl.submission_attempted = True

    if perform_validation(selected_values):
      inquirerControl.is_answered = True
      event.app.exit(result=selected_values)
  
  @binginds.add(Keys.Any)
  def other(_event):
    """Disallow inserting other text."""

  return Question(
    Application(
      layout=layout,
      key_bindings=bindings,
      style=merged_style,
      **utils.used_kwargs(kwargs, Application.__init__),
    )
  ) 
      