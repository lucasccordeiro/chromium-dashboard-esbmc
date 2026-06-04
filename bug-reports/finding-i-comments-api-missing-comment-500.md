# Finding I — upstream issue report (draft)

Ready-to-file GitHub issue for `GoogleChrome/chromium-dashboard`, formatted to the
repository's `bug_report.md` template. Verified against upstream `main` at commit
`3d6ec4bb` (2026-06-04). **Filed as [#6468](https://github.com/GoogleChrome/chromium-dashboard/issues/6468).**

- **Title:** `CommentsAPI` PATCH returns HTTP 500 (AttributeError) for an unknown `commentId`
- **Labels:** `bug`

---

**Describe the bug**

`PATCH /api/v0/features/<feature_id>/approvals/comments` (and the
`.../approvals/<gate_id>/comments` variant) returns **HTTP 500 Internal Server
Error** instead of **HTTP 404 Not Found** when the JSON body's `commentId` does
not correspond to an existing comment.

`CommentsAPI.do_patch` (`api/comments_api.py:165-177`):

```python
patch_request = PatchCommentRequest.from_dict(self.request.json)
comment: Activity = Activity.get_by_id(patch_request.comment_id)   # None if not found
user = self.get_current_user(required=True)
if not permissions.can_admin_site(user) and (
    comment and user.email() != comment.author):
    self.abort(403, msg='User does not have comment edit permissions')
if patch_request.is_undelete:
    comment.deleted_by = None           # line 175 — AttributeError if comment is None
else:
    comment.deleted_by = user.email()
```

`Activity.get_by_id(comment_id)` returns `None` when `commentId` is a valid id
with no matching comment (e.g. an already-deleted or never-existent comment). The
permission check does not stop this:
- for a site admin, `not permissions.can_admin_site(user)` is `False`, so the
  `and` short-circuits and no abort fires;
- for a non-admin, `(comment and …)` is falsy when `comment` is `None`, so the
  `and` is `False` and no abort fires.

Either way, control reaches `comment.deleted_by = …` on `None` → `AttributeError`.
`APIHandler.patch` (`framework/basehandlers.py:285`) has no `except` around
`do_patch`, so it becomes HTTP 500.

**To Reproduce**

Steps to reproduce the behavior:
1. As a signed-in user (the endpoint requires sign-in + XSRF), send:
   ```
   PATCH /api/v0/features/1/approvals/comments
   Content-Type: application/json

   {"commentId": 999999999, "isUndelete": true}
   ```
   (using a `commentId` that does not exist)
2. Observe **HTTP 500 Internal Server Error** (an `AttributeError: 'NoneType'
   object has no attribute 'deleted_by'` traceback) instead of HTTP 404.

**Expected behavior**

An unknown `commentId` should be rejected with **HTTP 404 Not Found**
(or HTTP 400), not produce an HTTP 500.

**Additional context**

- Affected code (commit `3d6ec4bb`): `api/comments_api.py:166` (`get_by_id`
  returns `None`), `:175`/`:177` (the `None` dereference);
  `framework/basehandlers.py:285` (`APIHandler.patch` has no `except`).
- Suggested fix:
  ```python
  comment = Activity.get_by_id(patch_request.comment_id)
  if comment is None:
      self.abort(404, msg='Comment not found')
  ```
- Same uncaught-exception → HTTP 500 class as PR #6451 and
  [#6464](https://github.com/GoogleChrome/chromium-dashboard/issues/6464); found by
  sweeping `api/` handlers for user input that reaches an uncaught exception.
  Confirmed with a standalone reproducer and an
  [ESBMC](https://github.com/esbmc/esbmc) bounded-model-checking harness.
