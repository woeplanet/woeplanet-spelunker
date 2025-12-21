"""
WOEplanet Spelunker: common package; languages module.
"""

import pycountry


def language_name(code: str) -> str:
    """
    Get the name of a language from an ISO 639 code
    """

    if code.lower() == 'unk':
        return 'Unknown'

    lang = pycountry.languages.get(bibliographic=code.lower())
    if not lang:
        lang = pycountry.languages.get(alpha_3=code.lower())

    return lang.name if lang else 'Unknown'
