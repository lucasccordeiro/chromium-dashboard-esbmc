#!/usr/bin/env python3
"""
Empirical reproducer — Finding I
  api/comments_api.py:175  CommentsAPI.do_patch
  Activity.get_by_id(comment_id) returns None for a missing/unknown commentId;
  the permission guard short-circuits, then `comment.deleted_by = ...` on None
  raises AttributeError → HTTP 500 (should be HTTP 404).

Source (verbatim, GoogleChrome/chromium-dashboard @ 4294104b):
  # api/comments_api.py:165-177
  patch_request = PatchCommentRequest.from_dict(self.request.json)
  comment: Activity = Activity.get_by_id(patch_request.comment_id)   ← None if not found
  user = self.get_current_user(required=True)
  if not permissions.can_admin_site(user) and (
      comment and user.email() != comment.author):
      self.abort(403, ...)                       ← short-circuits when comment is None
  if patch_request.is_undelete:
      comment.deleted_by = None                  ← AttributeError if comment is None
  else:
      comment.deleted_by = user.email()

Dependencies: none (pure Python stdlib).
"""

class Activity:
    _store = {}  # no comment with the requested id

    @classmethod
    def get_by_id(cls, comment_id):
        return cls._store.get(comment_id)   # None for an unknown id


def do_patch(comment_id, user_is_admin, user_email, is_undelete):
    """Inline of comments_api.py:165-177 (current code)."""
    comment = Activity.get_by_id(comment_id)            # None
    # Permission guard (short-circuits to no-abort when comment is None):
    if (not user_is_admin) and (comment and user_email != comment.author):
        return 403, 'no permission'
    # Dereference of a possibly-None comment:
    if is_undelete:
        comment.deleted_by = None                       # AttributeError on None
    else:
        comment.deleted_by = user_email
    return 200, 'Done'


for label, is_admin in [('site admin', True), ('regular user', False)]:
    try:
        do_patch(comment_id=999999999, user_is_admin=is_admin,
                 user_email='a@b.com', is_undelete=True)
        raise AssertionError('expected AttributeError')
    except AttributeError:
        print(f'do_patch(commentId=999999999) as {label} -> AttributeError '
              f'(None.deleted_by) -> propagates as HTTP 500')
print()

# Contrast — the fixed handler returns a clean 404.
def do_patch_fixed(comment_id):
    comment = Activity.get_by_id(comment_id)
    if comment is None:
        return 404, 'Comment not found'
    return 200, 'Done'


code, msg = do_patch_fixed(999999999)
print(f'fixed do_patch(commentId=999999999) -> HTTP {code} ({msg})')
assert code == 404
print()

print("CONFIRMED: PATCH .../approvals/comments with an unknown commentId raises")
print("  AttributeError -> HTTP 500 instead of HTTP 404.")
print()
print("Root cause: comments_api.py:166 get_by_id returns None; the 403 guard")
print("  short-circuits; comments_api.py:175/177 dereferences None.")
print("  APIHandler.patch (basehandlers.py:285) has no except around do_patch.")
print()
print("Proposed fix: if comment is None: self.abort(404, msg='Comment not found').")
