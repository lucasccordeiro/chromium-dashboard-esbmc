# Harness: api/comments_api.py:CommentsAPI.do_patch — Finding I
#
# Source: comments_api.py:165-177
#   patch_request = PatchCommentRequest.from_dict(self.request.json)
#   comment: Activity = Activity.get_by_id(patch_request.comment_id)   # None if not found
#   user = self.get_current_user(required=True)
#   if not permissions.can_admin_site(user) and (
#       comment and user.email() != comment.author):
#       self.abort(403, msg='User does not have comment edit permissions')
#   if patch_request.is_undelete:
#       comment.deleted_by = None           # AttributeError if comment is None
#   else:
#       comment.deleted_by = user.email()   # AttributeError if comment is None
#
# `Activity.get_by_id(comment_id)` returns None for a missing/unknown/None
# `commentId` (from the JSON body).  The permission guard does NOT stop this:
#   - for a site admin, `not can_admin_site(user)` is False → the `and`
#     short-circuits, no abort;
#   - for a non-admin, `(comment and ...)` is falsy when comment is None → the
#     `and` is False, no abort.
# Either way control reaches `comment.deleted_by = ...` on None → AttributeError.
# APIHandler.patch (basehandlers.py:285) has no `except` around do_patch(), so it
# becomes HTTP 500.  A missing comment should be HTTP 404 (or 400), not 500.
#
# Same bare-exception class as Finding A / G (PR #6451 convention).
#
# Expected verdict: FAILED (assertion `code == 404` violated via the exception
# path).
#
# Empirical reproduction:
#   PATCH /api/v0/features/1/approvals/comments   body: {"commentId": 999999999}
#   → HTTP 500 Internal Server Error  (expected: HTTP 404 Not Found)
#
# Proposed fix:
#   comment = Activity.get_by_id(patch_request.comment_id)
#   if comment is None:
#       self.abort(404, msg='Comment not found')


HTTP_200 = 200
HTTP_404 = 404
HTTP_500 = 500   # an uncaught AttributeError surfaces as HTTP 500


def comments_do_patch(comment_exists: int) -> int:
    """Inline model of CommentsAPI.do_patch (current code).

    The permission guard short-circuits to "no abort" when comment is None, so
    control always reaches `comment.deleted_by = ...`.  Dereferencing None raises
    AttributeError, which APIHandler.patch does not catch — modelled here as the
    HTTP 500 the caller observes.  (AttributeError is not an ESBMC-Python builtin,
    so the uncaught-exception outcome is represented by its HTTP code, mirroring
    how the abort paths model self.abort(4xx) as a returned code.)
    """
    # comments_api.py:175/177 — comment.deleted_by on a possibly-None comment.
    if not comment_exists:
        return HTTP_500   # None has no attribute 'deleted_by' → uncaught → 500.

    return HTTP_200


def main():
    comment_exists = nondet_int()  # noqa: F821  — did get_by_id find the comment?

    __ESBMC_assume(comment_exists == 0)  # noqa: F821  — missing/invalid commentId

    code = comments_do_patch(comment_exists)

    # Expected: a missing comment should yield HTTP 404.
    # Actual:   comment.deleted_by on None → AttributeError → HTTP 500.
    assert code == HTTP_404   # FAILS: code == HTTP_500 on the missing-comment path.


main()
