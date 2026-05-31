# Buggy: is_privacy_eligible — drop the explanation requirement.
# Expected verdict: FAILED (contract 1: result is True without explanation).


def is_privacy_eligible_buggy(
    explanation: bool,
    is_language_polyfill: bool,
    is_api_polyfill: bool,
    is_same_origin_css: bool,
) -> bool:
    """Buggy: drops the explanation check."""
    return is_language_polyfill or is_api_polyfill or is_same_origin_css


def main():
    explanation = nondet_bool()   # noqa: F821
    lang_poly   = nondet_bool()   # noqa: F821
    api_poly    = nondet_bool()   # noqa: F821
    same_origin = nondet_bool()   # noqa: F821

    result = is_privacy_eligible_buggy(explanation, lang_poly, api_poly, same_origin)

    # Contract 1: explanation required.
    if not explanation:
        assert not result   # FAILS: result can be True without explanation.


main()
