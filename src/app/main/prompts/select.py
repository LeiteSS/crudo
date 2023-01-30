# -*- coding: utf-8 -*-

from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Union

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from prompt_toolkit.styles import merge_styles

from main.utils import utils
from main.constants.constants import DEFAULT_QUESTION_PREFIX
from main.constants.constants import DEFAULT_SELECTED_POINTER
from main.constants.constants import DEFAULT_STYLE
from main.prompts import common
from main.prompts.common import Choice
from main.prompts.common import InquirerControl
from main.prompts.common import Separator
from main.model.question import Question

def select(
  message: str,
  choices: Sequence[Union[str, Choice, Dict[str, Any]]],
  default: Optional[Union[str, Choice, Dict[str, Any]]] = None,
  qmark: str = DEFAULT_QUESTION_PREFIX,
  pointer: Optional[str] = DEFAULT_SELECTED_POINTER,
  style: Optional[Style] = None,
  use_shortcuts: bool = False,
  use_arrow_keys: bool = True,
  use_indicator: bool = False,
  user_ws_keys: bool = True,
  use_emacs_keys: bool = True,
  show_selected: bool = False,
  instruction: Optional[str] = None,
  **kwargs: Any,
) -> Question:
  """A list of items to select **one** option from.
  
  The user can pick one option and confirm it (if you want to allow
  the user to select multiple options, use :meth:`questionary.checkbox` instead).

  Args:
      message: Question text

      choices: Items shown in the selection, this can contain :class:`Choice` or
               :class:`Separator`objects or simple items as strings. Passing
               :class:`Choice` objects, allows you to configure the item more
               (e.g. preselecting it or disabling it).
      
      default: A value corresponding to a selectable item in the choices,
               to initially set the pointer position to.
      
      qmark: Question prefix displayed in front of the question.
             By default this is a ``?``.
      
      pointer: Pointr symbol in front of the currently highlighted element.
               By default this is a ``>>``.
               use ``None`` to disable it.
      
      instruction: A hint on how to navigate the menu.
                   It's ``(Use shortcuts)`` if only ``use_shortcuts`` is set
                   to True, ``(Use arrow keys or shortcuts)`` if ``use_arrow_keys``
                   & ``use_shortcuts`` are set and ``(Use arrow keys)`` by default.
      
      style: A custom color and style for the question parts. You ca
             configure colors as well as font types for different elements.
      
      use_indicator: Flag to enable the small indicator in front of the
                     list highlighting the current location of the selection
                     cursor.
      
      use_shortcuts: Allow the user to select items from the list using
                     shortcuts. The shortcuts will be displayed in front of
                     the list items. Arrow keys , w/s keys and shortcuts are
                     mutually exclusive.
      
      use_arrow_keys: Allow the user to select items from the list using
                      arrow keys. Arrows keys, w/s keys and shortcuts are not
                      mutually exclusive.
      
      use_ws_keys: Allow the user to select items from the list using
                   `s` (down) and `w` (up) keys. Arrow keys, w/s keys and
                   shortcuts are not mutually exclusive.
      
      use_emacs_keys: Allow the user to select items from the list using
                      `Ctrl+N` (down) and `Ctrl+P` (up) keys. Arrow keys, w/s keys and
                      emacs keys and shortcuts are not mutually exclusive.
      
      show_selected: Display current selection choice at the bottom of list.
  
  Returns:
      :class:`Question`: Question instance, ready to be prompted (using ``.ask()``).
  """
  if not (use_arrow_keys or use_shortcuts or user_ws_keys or use_emacs_keys):
    raise ValueError(
      (
        "Some option to move the selection is required. "
        "Arrow keys, w/s keys, emacs keys, or shortcuts."
      )
    )
  
  if use_shortcuts and user_ws_keys:
    if any(getattr(choice, "shortcut_key", "") in ["j", "k"] for choice in choices):
      raise ValueError(
        "A choice is trying to register w/s as a "
        "shortcut key when they are in use as arrow keys "
        "disable one or the other."
      )
  
  if choices is None or len(choices) == 0:
    raise ValueError("A list of choices needs to be provided.")

  
  if use_shortcuts and len(choices) > len(InquirerControl.SHORTCUT_KEYS):
    raise ValueError(
      "A listwith shortcuts supports a maximum of {} "
      "choices as this is the maximum number "
      "of keyboard shortcuts that are available. You "
      "provided {} choices!"
      "".format(len(InquirerControl.SHORTCUT_KEYS), len(choices))
    )

  merged_style = merge_styles([DEFAULT_STYLE, style])

  inquirerControl = InquirerControl(
    choices,
    default,
    pointer=pointer,
    use_indicator=use_indicator,
    use_shortcuts=use_shortcuts,
    show_selected=show_selected,
    use_arrow_keys=use_arrow_keys,
    initial_choice=default,
  )

  def get_prompt_tokens():
    # noinspection PyListCreation
    tokens= [("class:qmark", qmark), ("class:question", " {} ".format(message))]

    if inquirerControl.is_answered:
      if isinstance(inquirerControl.get_pointed_at().title, list):
        tokens.append(
          (
            "class:answer",
            "".join([token[1] for token in inquirerControl.get_pointed_at().title]),
          )
        )
      else:
        tokens.append(("class:answer", inquirerControl.get_pointed_at().title))
    else:
      if instruction:
        tokens.append(("class:instruction", instruction))
      else:
        if use_shortcuts and use_arrow_keys:
          instruction_msg = "(Use shortcuts or arrow keys)"
        elif use_shortcuts and not use_arrow_keys:
          instruction_msg = "(Use shortcuts)"
        else:
          instruction_msg = "(Use arrow keys)"
        tokens.append(("class:instruction", instruction_msg))
    
    return tokens
  
  layout = common.create_inquirer_layout(inquireControl, get_prompt_tokens, **kwargs)

  bindings = KeyBindings()

  # Ctrl + Q or Ctrl + C
  @bindings.add(Keys.ControlQ, eager=True)
  @bindings.add(Keys.ControlC, eager=True)
  def _(event):
    event.app.exit(exception=KeyboardInterrupt, style="class:aborting")
  
  if use_shortcuts:
    # add key bindings for choices
    for inquire, choice in enumerate(inquirerControl.choices):
      if choice.shortcut_key is None and not choice.disabled and not use_arrow_keys:
        raise RuntimeError(
          "{} does not have a shortcut and arrow keys "
          "for movement are disabled. "
          "This choice is not reachable.".format(choice.title)
        )
      if isinstance(choice, Separator) or choice.shortcut_key is None:
        continue
    
      # noinspection PyShadowingNames
      def _reg_binding(inquire, keys):
        # trick out late evaluation with a "function factory":
        # source: https://stackoverflow.com/a/3431699
        @bindings.add(keys, eager=True)
        def select_choice(event):
          inquirerControl.pointed_at = inquire
        
        _reg_binding(inquire, choice.shortcut_key)
  
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
  
  if user_ws_keys:
    bindings.add("s", eager=True)(move_cursor_down)
    bindings.add("w", eager=True)(move_cursor_up)
  
  @bindings.add(Keys.ControlM, eager=True)
  def set_answer(event):
    inquirerControl.is_answered = True
    event.app.exit(result=inquirerControl.get_pointed_at().value)
  
  @bindings.add(Keys.Any)
  def other(event):
    """Disallow inserting other text."""
  
  return Question(
    Application(
      layout=layout,
      key_bindings=bindings,
      style=merged_style,
      **utils.used_kwargs(kwargs, Application.__init__),
    )
  )