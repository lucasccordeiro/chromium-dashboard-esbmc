#!/usr/bin/env python3
"""
Empirical reproducer — Finding F
  api/metricsdata.py:199  FeatureHandler.get_template_data
  get_int_arg('num') admits ?num=0; the `if num:` guard is falsy for 0, so the
  `properties[:num]` slice is skipped and the handler returns ALL datapoints.

Source (verbatim, GoogleChrome/chromium-dashboard @ d0d21c8):
  # api/metricsdata.py:197-214  FeatureHandler.get_template_data
  def get_template_data(self, **kwargs):
      num = self.get_int_arg('num')           ← admits 0
      if num and not self.should_refresh():   ← num=0 falsy → cache path skipped
          ...
      properties = self.fetch_all_datapoints()
      if num:                                 ← num=0 falsy → slice skipped
          properties = properties[:num]
      return _datapoints_to_json_dicts(properties)   ← returns ALL, HTTP 200

This is the inverse of Finding B (features ?num=0 → empty page): here ?num=0
returns the entire dataset.

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


num = get_int_arg('0')
print(f'get_int_arg("0") for ?num → {num!r}')
assert num == 0
print('  → 0 admitted.  No 400 issued.')
print()

# ── Step 2: get_template_data with num=0 returns every datapoint ──────────

def fetch_all_datapoints():
    """Model of fetch_all_datapoints(): the full set in the datastore."""
    return ['dp1', 'dp2', 'dp3', 'dp4', 'dp5']


def should_refresh():
    return False


def get_template_data(num_arg):
    """Inline of api/metricsdata.py:197-214 (cache miss)."""
    num = get_int_arg(num_arg)              # admits 0
    if num and not should_refresh():        # num=0 falsy → cache lookup skipped
        pass
    properties = fetch_all_datapoints()
    if num:                                 # num=0 falsy → slice skipped
        properties = properties[:num]
    return 200, properties


code, props = get_template_data('0')
print(f'get_template_data(num=0) → HTTP {code}')
print(f'  returned {len(props)} datapoints: {props}')
print()

assert code == 200
# ?num=0 returns ALL datapoints — the requested limit of 0 is ignored.
assert props == ['dp1', 'dp2', 'dp3', 'dp4', 'dp5']
assert len(props) > 0          # caller asked for top-0, got the whole set

# ── Step 3: contrast — the fixed guard honors the limit ───────────────────

def get_template_data_fixed(num_arg):
    """With `if num is not None:` — a provided limit is always applied."""
    num = get_int_arg(num_arg)
    properties = fetch_all_datapoints()
    if num is not None:                     # FIX: honor num even when 0
        properties = properties[:num]
    return 200, properties


code_fixed, props_fixed = get_template_data_fixed('0')
print(f'fixed get_template_data(num=0) → HTTP {code_fixed}')
print(f'  returned {len(props_fixed)} datapoints: {props_fixed}')
assert props_fixed == []       # top-0 is empty, as requested
print()

# ── Summary ───────────────────────────────────────────────────────────────

print('CONFIRMED: GET /api/v0/data/featurepopularity?num=0 returns HTTP 200 with')
print('  ALL datapoints instead of the requested top-0 (empty) list.')
print()
print('Root cause:')
print('  basehandlers.py:193  `if num < 0: self.abort(400, ...)`  admits num=0.')
print('  metricsdata.py:208   `if num:`  is falsy for 0, so `properties[:num]`')
print('  is skipped and the full dataset is returned.')
print()
print('Proposed fix:')
print('  Replace `if num:` with `if num is not None:` so a provided limit')
print('  (including 0) always bounds the result.')
