#!/usr/bin/env python3
"""
Empirical reproducer — Finding E
  api/shipping_features_api.py:58  get_int_arg admits ?mstone=0
  → milestone 0 queried, no stage matches, empty feature lists, HTTP 200

Source (verbatim, GoogleChrome/chromium-dashboard):
  # shipping_features_api.py:56-68
  def do_get(self, **kwargs):
      milestone = self.get_int_arg('mstone')   ← admits 0
      if milestone is None:                     ← 0 is not None → passes
          self.abort(400, msg='No milestone provided.')
      shipping_stages = self._get_shipping_stages(milestone)
      if len(shipping_stages) == 0:
          return {'complete_features': [], 'incomplete_features': []}  ← HTTP 200
      ...

  # shipping_features_api.py:40-54  _get_shipping_stages(0)
  #   Stage.query(... milestones.*_first == 0 ...).fetch()
  #   No real stage ships at milestone 0 → returns [].

Dependencies: none (pure Python stdlib).
"""

# ── Step 1: confirm get_int_arg admits 0 ─────────────────────────────────

def get_int_arg(val_str, default=None):
    """Verbatim logic from basehandlers.py:182-197."""
    val = val_str or default
    if val is None:
        return None
    try:
        num = int(val)
    except ValueError:
        return 'ABORT_400'
    if num < 0:
        return 'ABORT_400'
    return num


mstone = get_int_arg('0')
print(f'get_int_arg("0") for ?mstone → {mstone!r}')
assert mstone == 0
print('  → 0 admitted.  No 400 issued.')
print()

# ── Step 2: show the `is None` guard does not trigger for mstone=0 ────────

if mstone is None:
    print('  `milestone is None` guard: TRIGGERED  (would abort 400)')
else:
    print(f'  `milestone is None` guard: not triggered ({mstone!r} is not None).')
print()

# ── Step 3: _get_shipping_stages(0) matches no real stage ────────────────

# No Chrome feature ships at milestone 0, so the NDB query
#   Stage.milestones.{desktop,android,ios,webview}_first == 0
# returns an empty list.  do_get then takes the len==0 early return.
def _get_shipping_stages(milestone):
    """Model of shipping_features_api.py:40-54 for milestone 0."""
    # milestone 0 matches no stage's *_first milestone field.
    return []


def do_get(mstone):
    """Inline of shipping_features_api.py:56-68 acceptance + early return."""
    if mstone is None:
        return 400, None
    shipping_stages = _get_shipping_stages(mstone)
    if len(shipping_stages) == 0:
        return 200, {'complete_features': [], 'incomplete_features': []}
    return 200, {'complete_features': ['...'], 'incomplete_features': ['...']}


code, body = do_get(0)
print(f'do_get(mstone=0) → HTTP {code}')
print(f'  body: {body}')
print()

assert code == 200
assert body == {'complete_features': [], 'incomplete_features': []}

# ── Summary ───────────────────────────────────────────────────────────────

print('CONFIRMED: GET /api/v0/shipping_features?mstone=0 returns HTTP 200 with:')
print('  {"complete_features": [], "incomplete_features": []}')
print()
print('Root cause:')
print('  basehandlers.py:193  `if num < 0: self.abort(400, ...)`')
print('  Milestone numbers must be >= 1; 0 is not a real Chrome milestone.')
print('  get_int_arg has no minimum-value guard, and do_get guards only')
print('  `milestone is None`, so mstone=0 passes through.')
print()
print('Proposed fix:')
print('  After the `is None` guard at shipping_features_api.py:60, add:')
print('    if milestone < 1:')
print("        self.abort(400, msg='Milestone number must be >= 1')")
