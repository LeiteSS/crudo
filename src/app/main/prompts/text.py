from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

# prompt_toolkit us a library for building powerful interactive command line and terminal
# applications in Python. 
# source: https://python-prompt-toolkit.readthedocs.io/en/master/
from prompt_toolkit.document import Document
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.shortcuts.prompt import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.styles import merge_styles

from main.constants.constants import DEFAULT_QUESTION_PREFIX
from main.constants.constants import DEFAULT_STYLE
from main.constants.constants import FINISH_INSTRUCTION_MULTILINE
from main.prompts.common import build_validator
from main.model.question import Question

def text(
  message: str,
  default: str = "",
  validate: Any = None,
  qmark: str = DEFAULT_QUESTION_PREFIX,
  style: Optional[Style] = None,
  multiline: bool = False,
  instruction: Optional[str] = None,
  lexer: Optional[Lexer] = None,
  **kwargs: Any,
) -> Question:
    """Prompt the user to ente a free text message.

    This question type can be used to prompt the user for some text input.

    Args:
        message: Question text.

        default: Default value will be returned if the user just hits enter.

        validate: Require the entered value to pass a validation. The value
                  can not be submitted until the validator accepts it 
                  (e.g. to check minimum password legth).

                  This can either be a function accepting the input and
                  returning a boolean, or an class reference to a
                  subclass of the prompt toolkit Validator class.
        
        qmark: Question prefix displayed in front of the question. By default
               this is a ``?``.
        
        style: A custom color and style for the question parts. You can
               configure colors as well as font types for different elements.

        multiline: If ``True``, multiline input will be enabled.

        instruction: Write instructions for the user if needed. If ``None``
                     and ``multiline=True``, some instructions will appear.

        lexer: Supply a valid lexer to style the answer. Leave empty to
               use a simple one by default.

        kwargs: Additional arguments, they will be passed to prompt toolkit. 

    Returns:
        :class:`Question`: Question instance, ready to be prompted (using ``.ask()``).
    """

    merged_styles = merge_styles([DEFAULT_STYLE, style])
    lexer = lexer or SimpleLexer("class:answer")
    validator = build_validator(validate)

    if instruction is None and multiline:
        instruction = INSTRUCTION_MULTILINE
    
    def get_prompt_tokens() -> List[Tuple[str, str]]:
      result = [("class:qmark", qmark), ("class:question", " {} ".format(message))]
      if instruction:
          result.append(("class:instruction", " {} ".format(instruction)))
      return result

    promptSession = PromptSession(
        get_prompt_tokens,
        style=merged_styles,
        validator=validator,
        lexer=lexer,
        multiline=multiline,
        **kwargs,
    )

    promptSession.default_buffer.reset(Document(default))

    return Question(promptSession.app)