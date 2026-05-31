# Harness: internals/self_certify.py:is_privacy_eligible
#
# Contract: True iff `explanation AND (language_polyfill OR api_polyfill OR same_origin_css)`.
# Source: self_certify.py:73-79.

def is_privacy_eligible(
    explanation: bool,
    is_language_polyfill: bool,
    is_api_polyfill: bool,
    is_same_origin_css: bool,
) -> bool:
    """Inline of self_certify.is_privacy_eligible."""
    return explanation and (
        is_language_polyfill or is_api_polyfill or is_same_origin_css
    )


def main():
    explanation = nondet_bool()          # noqa: F821
    lang_poly   = nondet_bool()          # noqa: F821
    api_poly    = nondet_bool()          # noqa: F821
    same_origin = nondet_bool()          # noqa: F821

    result = is_privacy_eligible(explanation, lang_poly, api_poly, same_origin)

    # Contract 1: requires explanation.
    if not explanation:
        assert not result

    # Contract 2: requires at least one polyfill type.
    if not (lang_poly or api_poly or same_origin):
        assert not result

    # Contract 3: both conditions together are sufficient.
    if explanation and (lang_poly or api_poly or same_origin):
        assert result

    # Contract 4: result equals the full boolean expression.
    assert result == (explanation and (lang_poly or api_poly or same_origin))


main()
