from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit import print_formatted_text
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea


styles = {
    "main": "#ffffff bold",
    "normal": "#29bf12",
    "error": "#f71735",
    "info": "#d1d8df",
    "attention": "#ffffff bold",
    "warning": "#fcf622 italic",
    "prompt": "#00bbf9",
}

prefixes = {
    "main": "\n",
    "normal": "-> result: ",
    "error": "-> error: ",
    "info": "\n-> task: ",
    "attention": "\n: ",
    "warning": "\nwarning! ",
    "prompt": "",
}


suffixes = {
    "main": "\n",
    "normal": "\n",
    "error": "\n",
    "info": "",
    "attention": " :",
    "warning": "\n",
    "prompt": "",
}

style_template = Style.from_dict(styles)


def format_text(text, style, err=False):

    if style in styles:
        prefix = prefixes.get(style)
        suffix = suffixes.get(style)
        text_template = f"class:{style}"
        text = FormattedText(
            [(text_template, prefix), (text_template, text), (text_template, suffix)]
        )
        return text

    return None


def print_cli(out, err=None, style="info", mode="text"):

    if out:
        text = format_text(out, style)
    elif err:
        text = format_text(err, style, err=True)
    else:
        text = None

    if text:

        if mode == "text":
            print_formatted_text(text, style=style_template)
