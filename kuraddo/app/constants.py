from main import Style

YES = "Yes"
NO = "No"
YES_OR_NO = "[Y/n]"
NO_OR_YER = "[y/N]"
FINISH_INSTRUCTION_MULTILINE = "[Finish with 'Alt+Enter' or 'Esc then Enter']\n>"
DEFAULT_SELECTED_POINTER = ">>"
INDICATOR_SELECTED = "●"
INDICATOR_UNSELECTED = "○"
DEFAULT_QUESTION_PREFIX = "?"
DEFAULT_CANCEL_MESSAGE = "Operation cancelled by user"
INVALID_INPUT = "Invalid Input"
DEFAULT_STYLE = Style(
  [
    ("qmark", "fg:#5f819d"),
    ("question", "bold"),
    ("answer", "fg:#FF9D00 bold"),
    ("pointer", ""),
    ("selected", ""),
    ("instruction", ""),
    ("text", ""),
  ]
)
