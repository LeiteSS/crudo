"""
  @Author: Silas S Leite
  @Date: January 29, 2023
  @Description: Some functions those are done often during the CLI usage
"""

# Inspect live object - It can help you examine the contnts of a class, retrieve the source
# code of a method, extract and format the argument list for a function, or get all the 
# information you need to display a detailed traceback.
# source: https://docs.python.org/3/library/inspect.html
import inspect

# Data Structures
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

# prompt_toolkit us a library for building powerful interactive command line and terminal
# applications in Python. 
# source: https://python-prompt-toolkit.readthedocs.io/en/master/
from prompt_toolkit import PromptSession
from prompt_toolkit.filters import Always
from prompt_toolkit.filters import Condition
from prompt_toolkit.filters import IsDone
from prompt_toolkit.layout import ConditionalContainer
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout import Window
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.validation import Validator
from prompt_toolkit import print_formatted_text as pt_print
from prompt_toolkit.formatted_text import FormattedText as FText


# Constants

from main.constants.constants import DEFAULT_SELECTED_POINTER
from main.constants.constants import DEFAULT_STYLE
from main.constants.constants import INDICATOR_SELECTED
from main.constants.constants import INDICATOR_UNSELECTED
from main.constants.constants import INVALID_INPUT

# Cut-down version of 'prompt_toolkit.formatted_text.AnyFormattedText"
# source: Questionary
FormattedText = Union[
  str,
  List[Tuple[str, str]],
  List[Tuple[str, str, Callable[[Any], None]]],
  None,
]

class Choice:
  """One choice in a :meth:`select`, :meth:`rawselect` or :meth:`checkbox`,

  Args:
      title: Text show in the selection list

      value: Value returne, when the choice is selected. If this argument
             is `None` or unset, the the value of `title` is used.
    
      disabled: If set, the choice can not be selected by the user.

      checked: Preselect this choice whn displaying the options.

      shotcut_key: Key shortcut used to select this item.
  """
  title: FormattedText
  """ Title of the Choice """

  value: Optional[Any]
  """ Values of the choice; optional because it can be null """

  disabled: Optional[str]
  """ Whether the choice can be selected """

  checked: Optional[bool]
  """ Whether the choice is initially selected """

  shortcut_key: Optional[str]
  """ A shortcut key for the choice """

# constructor
  def __init__(
    self, 
    title: FormattedText, 
    value: Optional[Any] = None, 
    disabled: Optional[str] = None,
    checked: Optional[bool] = False,
    shortcut_key: Optional[Union[str, bool]] = True,
  ) -> None:
      self.disabled = disabled
      self.title = title

      # If checked is equal to true or  equal to false, cannot be equal to None
      self.checked = checked if checked is not None else False

      # instance() function - returns True if the specified object is of the specified
      # type, otherwise False. If the type parameter is a tuple, this function will 
      # return True if the object is one of the types in the tuple.
      # source: https://www.w3schools.com/python/ref_func_isinstance.asp
      if value is not None:
          self.value = value
      elif isinstance(title, list):
          self.value = "".join([token[1] for token in title])
      else:
          self.value = title
      
      if shortcut_key is not None:
          if isinstance(shortcut_key, bool):
              self.auto_shortcut = shortcut_key
              self.shortcut_key = None
          else:
              self.shortcut_key = None
              self.auto_shortcut = True

  @staticmethod
  def build(choice: Union[str, "Choice", Dict[str, Any]]) -> "Choice":
      """Create a choice object from different representations.

      Args:
          choice: Either a :obj:`str`, :class:`Choice` or :obj:`Dict` with
              ``name``, ``value``, ``disabled``, ``checked`` and
              ``key`` properties.
      Returns:
          An instance of the :class:`Choice`object.
      """

      if isinstance(choice, Choice):
          return choice
      elif isinstance(choice, str):
          return Choice(choice, choice)
      else:
          return Choice(
            choice.get("name"),
            choice.get("value"),
            choice.get("disabled", None),
            choice.get("checked"),
            choice.get("key"),
          )
  
  def get_shortcut_key_title(self):
      """Get Shortcut Key Title

      Args:
          self: It will used the attribute shortcut_key 
      
      Returns:
          -) when None or shortcut_key) that can be A), B), C), 1), 2), 3), etc.
      """
      if self.shortcut_key is None:
          return "-) "
      else:
          return "{}) ".format(self.shortcut_key)

class Separator(Choice):
      """Used to separate choices group."""

      default_separator: str = "-" * 15
      """The default separator used if none is specified"""

      line: str
      """The string being used as a separator"""

      def __init__(self, line: Optional[str] = None) -> None:
          """Create a separator in a list.

          Args:
              line: Text to be displayed in the list, by default uses ``-``
          """

          self.line = line or self.default_separator
          super().__init__(self.line, None, "-")

class InquirerControl(FormattedTextControl):
    """Inquirer mean a person who asks for information, this class control the questions and choice"""

    SHORTCUT_KEYS = [
      "1",
      "2",
      "3",
      "4",
      "5",
      "6",
      "7",
      "8",
      "9",
      "0",
      "a",
      "b",
      "c",
      "d",
      "e",
      "f",
      "g",
      "h",
      "i",
      "j",
      "k",
      "l",
      "m",
      "n",
      "o",
      "p",
      "q",
      "r",
      "s",
      "t",
      "u",
      "v",
      "w",
      "x",
      "y",
      "z",
      "A",
      "B",
      "C",
      "D",
      "E",
      "F",
      "G",
      "H",
      "I",
      "J",
      "K",
      "L",
      "M",
      "N",
      "O",
      "P",
      "Q",
      "R",
      "S",
      "T",
      "U",
      "V",
      "W",
      "X",
      "Y",
      "Z"
    ]

    choices: List[Choice]
    default: Optional[Union[str, Choice, Dict[str, Any]]]
    selected_options: List[Any]
    use_indicator: bool
    use_shortcuts: bool
    use_arrow_keys: bool
    pointer: Optional[str]
    pointed_at: int
    is_answered: bool

    def __init__(
      self,
      choices: Sequence[Union[str, Choice, Dict[str, Any]]],
      default: Optional[Union[str, Choice, dict[str, Any]]] = None,
      pointer: Optional[str] = DEFAULT_SELECTED_POINTER,
      use_indicator: bool = True,
      use_shortcuts: bool = False,
      show_selected: bool = False,
      use_arrow_keys: bool = True,
      initial_choice: Optional[Union[str, Choice, Dict[str, Any]]]= None,
      **kwargs: Any,
    ):
        self.use_indicator = use_indicator
        self.use_shortcuts = use_shortcuts
        self.show_selected = show_selected
        self.use_arrow_keys = use_arrow_keys
        self.default = default
        self.pointer = pointer

        if isinstance(default, Choice):
            default = defaulf.value
        
        choices_values = [
            choice.value for choice in choices if isinstance(choice, Choice)
        ]

        if (
          default is not None
          and default not in choices
          and default not in choices_values
        ): 
            raise ValueError(
              f"Invalid `default` value passed. The value (`{default}`) "
              f"does not exists in the set of choices. Please make sure the "
              f"default value is one of the available choices."
            )
        
        if initial_choice is None:
            pointed_at = None
        elif initial_choice in choices:
            pointed_at = choices.index(initial_choice)
        elif initial_choice in choices_values:
            for k, choice in enumerate(choices):
                if isinstance(choice, Choice):
                    if choice.value == initial_choice:
                        pointed_at = k
                        break
        
        else:
            raise ValueError(
              f"Invalid `initial_choice` value passed. The value"
              f"(`{initial_choice}`) does not exist in "
              f"the set of choices. Please make sure the initial value is "
              f"one of the available choices."
            )
        
        self.is_answered = False
        self.choice = []
        self.submission_attempted = False
        self.error_message = None
        self.selected_options = []

        self._init_choices(choices, pointed_at)
        self._assign_shortcut_keys()

        super().__init__(self._get_choice_tokens, **kwargs)

        if not self.is_selection_valid():
            raise ValueError(
              f"Invalid 'initial_choice' value (`{initial_choice}`). "
              f"It must be a selectable value."
            )
    
    # pythonic way to use getters and setters in object-oriented programming;
    # source: https://www.programiz.com/python-programming/property
    def choice_count(self) -> int:
        return len(self.choices)

    # Private Operations

    def _is_selected():
        if isinstance(self.default, Choice):
            compare_default = self.default == choice
        else:
            compare_default = self.default == choice.value
        return choice.checked or compare_default and self.default is not None
    
    def _assign_shortcut_keys(self):
        available_shortcuts = self.SHORTCUT_KEYS[:]

        # make sure we do not double assign a shortcut
        for choice in self.choices:
            if choice.shortcut_key is not None:
                if choice.shortcut_key in available_shortcuts:
                    available_shortcuts.remove(choice.shortcut_key)
                else:
                    raise ValueError(
                        "Invalid shortcut '{}'"
                        "for choice '{}'. Shortcuts "
                        "should be single characters or number. "
                        "Make sure that all your shortcuts are "
                        "unique.".format(choice.shortcut_key, choice.title)
                    )
        
        shortcut_index = 0
        for choice in self.choices:
            if choice.auto_shortcut and not choice.disabled:
                choice.shortcut_key = available_shortcuts[shortcut_index]
                shortcut_index += 1
            
            if shortcut_index == len(available_shortcuts):
                break 
        
    def _init_choices(
      self,
      choices: Sequence[Union[str, Choice, Dict[str, Any]]],
      pointed_at: Optional[int],
    ):
        # helper to convert from question format to internal format
        self.choices = []

        if pointed_at is not None:
          self.pointed_at = pointed_at
        
        for index, choice in enumerate(choices):
            choice = Choice.build(choice)

            if self._is_selected(choice):
                self.selected_options.append(choice.value)
            
            if pointed_at is None and not choice.disabled:
                self.pointed_at = pointed_at = index
            
            self.choices.append(choice)
    
   
    
    def _get_choice_tokens(self):
      tokens = []

      def append(index: int, choice: Choice):
          # use value to check if option has been selected
          selected = choice.value in self.selected_options

          if index == self.pointed_at:
              if self.pointer is not None:
                  tokens.append(("class:ponter", " {}".format(self.pointer)))
              else:
                  tokens.append(("class:text", " " * 3))
              
              tokens.append(("[SetCursorPosition]", ""))
          else:
              pointer_length = len(self.pointer) if self.pointer is not None else 1
              token.append(("class:text", " " * (2 + pointer_length)))
          
          if isinstance(choice, Separator):
              tokens.append(("class:separator", "{}".format(choice.title)))
          elif choice.disabled:
              if isinstance(choice.title, list):
                  tokens.append(
                      ("class:selected" if selected else "class:disabled", "- ")
                  )
                  tokens.extend(choice.title)
              else:
                  tokens.append(
                      (
                        "class:selected" if selected else "class:disabled",
                        "- {}".format(choice.title)
                      )
                  )
              
              tokens.append(
                  (
                      "class:selected" if selected else "class:disabled",
                      "{}".format(
                          ""
                          if isinstance(choice.disabled, bool)
                          else " ({})".format(choice.disabled)
                      ),
                  )
              )
          else:
              shortcut = choice.get_shortcut_key_title() if self.use_shortcuts else ""

              if selected:
                  if self.use_indicator:
                      indicator = INDICATOR_SELECTED + " "
                  else:
                      indicator = ""
                  
                  tokens.append(("class:selected", "{}".format(indicator)))
              else:
                  if self.use_indicator:
                      indicator = INDICATOR_UNSELECTED + " "
                  else:
                      indicator = ""
                  
                  tokens.append(("class:text", "{}".format(indicator)))
              
              if isinstance(choice.title, list):
                  tokens.extend(choice.title)
              elif selected:
                  tokens.append(
                      ("class:selected", "{}{}".format(shortcut, choice.title))
                  )
              elif index == self.pointed_at:
                  tokens.append(
                      ("class:highlighted", "{}{}".format(shortcut, choice.title))
                  )
              else:
                  tokens.append(("class:text", "{}{}".format(shortcut, choice.title)))
          tokens.append(("", "\n"))
      
      # prepare the select choices
      for index, choice in enumerate(self.choices):
          append(index, choice)
      
      if self.show_selected:
            current = self.get_pointed_at()

            answer = current.get_shortcut_title() if self.use_shortcuts else ""

            answer += (
                current.title if isinstance(current.title, str) else current.title[0][1]
            )

            tokens.append(("class:text", " Answer: {}".format(answer)))
      else:
          tokens.pop() # Remove last newline
      
      return tokens
  
    def is_selection_a_separator(self) -> bool:
        selected = self.choices[self.pointed_at]

        return isinstance(selected, Separator)

    def is_selection_disabled(self) -> Optional[str]:
        return self.choices[self.pointed_at].disabled

    def is_selection_valid(self) -> None:
        return not self.is_selection_disabled() and not self.is_selection_a_separator()

    def select_previous(self) -> None:
        self.pointed_at = (self.pointed_at - 1) % self.choice_count
    
    def select_next(self) -> None:
        self.pointed_at = (self.pointed_at + 1) % self.choice_count
    
    def get_pointed_at(self) -> Choice:
        return self.choice[self.pointed_at]
    
    def get_selected_values(self) -> List[Choice]:
        return [
            choice
            for choice in self.choices
            if (not isinstance(choice, Separator) and choice.value in self.selected_options)
        ]
 

def build_validator(validate: Any) -> Optional[Validator]:
    if validate:
        if inspect.isclass(validate) and issubclass(validate, Validator):
            return validate()
        elif isinstance(validate, Validator):
            return validate
        elif callable(validate):

            class _InputValidator(Validator):
                def validate(self, document):
                    verdict = validate(document.text)

                    if verdict is not True:
                        if verdict is False:
                            verdict = INVALID_INPUT
                        raise ValidationError(
                            message=verdict, cursor_position=len(document.text)
                        )
            
            return _InputValidator()
    return None

def create_inquirer_layout(
  inquireControl: InquirerControl,
  get_prompt_tokens: Callable[[], List[Tuple[str, str]]],
  **kwargs: Any,
) -> Layout:
    """Create a layout combining question and inquirer selection."""
    promptSession = PromptSession(get_prompt_tokens, reserve_space_for_menu=0, **kwargs)
    _fix_unessary_blank_lines(promptSession)

    validation_prompt = PromptSession(bottom_toolbar=lambda: inquireControl.error_message, **kwargs)

    return Layout(
        HSplit(
            [
                promptSession.layout.container,
                ConditionalContainer(Window(inquireControl), filter=~IsDone()),
                ConditionalContainer(
                    validation_prompt.layout.container,
                    filter=Condition(lambda: inquireControl.error_message is not None),
                ),
            ]
        )
    )

def print_formatted_text(text: str, style: Optional[str] = None, **kwargs: Any) -> None:
    """Print formatted text.

    Allow to include special characters in the text.

    Args:
        text: Text to be printed.
        style: Style used for printing. The style argument uses the
            prompt :ref:`toolkit style strings <prompt_toolkit:styling>`.
    """
    if style is not None:
        text_style = Style(["text", style])
    else:
        text_style = DEFAULT_STYLE
    
    pt_print(FText([("class:text", text)]), style=text_style, **kwargs)


def _fix_unessary_blank_lines(promptSession: PromptSession) -> None:
    """This is a fix for additional empty lines added by prompt toolkit.

    This assumes the layout of the default session doesn't change, if it
    does, this need an update. """

    default_container = promptSession.layout.container

    default_buffer_window = (
        default_container.get_children()[0].content.get_children()[1].content
    )

    assert isinstance(default_buffer_window, Window)

    # this forces the main window to stay as small as possible, avoiding
    # empty lines in selections
    default_buffer_window.dont_extend_height = Always()
    default_buffer_window.always_hide_cursor = Always()
      


