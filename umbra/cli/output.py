from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit import print_formatted_text


styles = {
    "main": "#f8af2c",
    "normal": "#b2df4b",
    "error": "#a693c9 bold",
    "info": "#63a8df",
    "attention": "#ffe400",
    "warning": "#fed1ff italic",
}

style_template = Style.from_dict(styles)


def format_text(text, style, err=False):

    if style in styles:
        text_template = f"class:{style}"
        text = FormattedText([(text_template, text)])
        return text

    return None


def print_cli(out, err=None, style="info"):

    if out:
        text = format_text(out, style)
    elif err:
        text = format_text(err, style, err=True)
    else:
        text = None

    if text:
        print_formatted_text(text, style=style_template)
