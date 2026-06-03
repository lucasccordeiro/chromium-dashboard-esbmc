# Harness: api/comments_api.py:CommentsAPI.do_patch — Finding I (fix)
#
# Positive control / paired good harness for Finding I
# (`comments_patch_missing_comment_http500.py`).  Models the proposed fix: check
# that the comment exists before dereferencing it.
#
#   comment = Activity.get_by_id(patch_request.comment_id)
#   if comment is None:
#       self.abort(404, msg='Comment not found')    # FIX
#   ...
#   comment.deleted_by = ...
#
# With the existence guard, a missing/unknown commentId yields HTTP 404, never an
# uncaught AttributeError (HTTP 500).
#
# Expected verdict: SUCCESSFUL (Phase 1 and Phase 2).


HTTP_200 = 200
HTTP_404 = 404


def comments_do_patch_fixed(comment_exists: int) -> int:
    """Model of do_patch with the comment-existence guard added."""
    # Fix: reject a missing comment with abort(404) before dereferencing it.
    if not comment_exists:
        return HTTP_404
    return HTTP_200


def main():
    comment_exists = nondet_int()  # noqa: F821

    code = comments_do_patch_fixed(comment_exists)

    # Every case yields a clean HTTP code (never throws).
    assert code == HTTP_404 or code == HTTP_200
    # A missing comment is rejected with HTTP 404, not 500.
    if not comment_exists:
        assert code == HTTP_404


main()
