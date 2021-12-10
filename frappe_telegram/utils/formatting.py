import re


def strip_unsupported_html_tags(txt: str) -> str:
    """
    Only a set of formatting options are supported
    https://core.telegram.org/bots/api#formatting-options
    """
    tags_supported = [
        "b", "strong",              # Bold
        "i", "em",                  # Italics
        "u", "ins",                 # Underline
        "s", "strike", "del",       # Strikethrough
        "a",                        # Links
        "pre", "code",              # Code
    ]

    # Replace Unsupported Tags
    """
    < /?                    # Permit closing tags
    (?!
        (?: em | strong )   # List of tags to avoid matching
        \b                  # Word boundary avoids partial word matches
    )
    [a-z]                   # Tag name initial character must be a-z
    (?: [^>"']              # Any character except >, ", or '
    | "[^"]*"               # Double-quoted attribute value
    | '[^']*'               # Single-quoted attribute value
    )*
    >

    https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch09s04.html
    """
    r = """</?(?!(?:{})\\b)[a-z](?:[^>"']|"[^"]*"|'[^']*')*>""".format("|".join(tags_supported))
    txt = re.sub(
        pattern=r,
        repl="",
        string=txt)

    #   &   &amp;
    txt = txt.replace("&", "&amp;")

    #   <   &lt;
    txt = re.sub(
        pattern=r"<(?!(?:[a-z]+|\/[a-z]+)\b)",
        repl="&lt;",
        string=txt,
    )

    #   >   $gt;
    # Seems to go through well

    return txt
