# -*- coding: utf-8 -*-
# This module provides regular expression matching operations similar to those found in Perl.
# source: https://docs.python.org/3/library/re.html
import re

from prompt_toolkit.validation import ValidationError
from prompt_toolkit.validation import Validator

from tests.utils import feed_cli_with_input

def test_legacy_name():
    message = "What is your name"
    text = "joe doe\r"

    result, cli = feed_cli_with_input("input", message, text)
    
    assert result == "joe doe"

def test_text():
    message = "what is your name"
    text = "joe doe\r"

    result, cli = feed_cli_with_input("text", message, text)

    assert result == "joe doe"

def test_text_validate():
    message = "what is your name"
    text = "Joe doe\r"

    result, cli = feed_cli_with_input(
      "text",
      message,
      text,
      validate=lambda val: val == "Joe doe" or "is your name Joe doe?",
    )

    assert result == "Joe doe"

def test_text_validate_with_class():
    class SimpleValidator(Validator):
        def validate(self, document):
            ok = re.match("[01][01][01]", document.text)
            if not ok:
                raise ValidationError(
                  message="Binary FTW", cursor_position=len(document.text)
                )
    
    message = "What is your name"
    text = "001\r"

    result, cli = feed_cli_with_input("text", message, text, validate=SimpleValidator)

    assert result == "001"