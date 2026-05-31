#!/usr/bin/env python3
"""
Empirical reproducer — Finding B
  api/features_api.py:117  get_int_arg admits ?num=0 → silent empty page, HTTP 200

Source (verbatim, d0d21c8):
  # basehandlers.py:182-197  get_int_arg
  def get_int_arg(self, name, default=None) -> int | None:
      val = self.request.args.get(name, default) or default
      if val is None:
          return None
      try:
          num = int(val)
      except ValueError:
          self.abort(400, msg='Request parameter %r was not an int' % name)
      if num < 0:
          self.abort(400, msg='Request parameter %r out of range: %r' % (name, val))
      return num      ← 0 is returned here; no positivity guard

  # features_api.py:117-118
  num   = self.get_int_arg('num', search.DEFAULT_RESULTS_PER_PAGE)  # = 100
  start = self.get_int_arg('start', 0)

  # search.py:471  process_query_using_cache
  num = min(num, MAX_RESULTS_PER_PAGE)   # min(0, 1000) = 0
  ...
  paginated_id_list = sorted_id_list[start : start + num]   # [0:0] = []

  → {"total_count": N, "features": []}  HTTP 200  — no 400 error signal

Dependencies: none (pure Python stdlib).
"""

# ── Step 1: inline get_int_arg and confirm 0 is admitted ─────────────────

def get_int_arg(val_str, default=None):
    """
    Verbatim logic from basehandlers.py:182-197.
    Returns 'ABORT_400' where the real code calls self.abort(400, ...).
    """
    val = val_str or default          # '0' is truthy → val = '0'
    if val is None:
        return None
    try:
        num = int(val)
    except ValueError:
        return 'ABORT_400'
    if num < 0:
        return 'ABORT_400'
    return num                        # 0 passes through: not None, not < 0


result = get_int_arg('0', default=100)
print(f'get_int_arg("0", default=100) → {result!r}')
assert result == 0, f'Expected 0, got {result!r}'
print('  → 0 returned (HTTP 200 path).  No 400 issued.')
print()

# ── Step 2: show the downstream effect in process_query_using_cache ──────

DEFAULT_RESULTS_PER_PAGE = 100
MAX_RESULTS_PER_PAGE     = 1000

def simulate_query(start, num, total_ids):
    """Inline of the pagination slice in search.py."""
    num = min(num, MAX_RESULTS_PER_PAGE)           # min(0, 1000) = 0
    paginated = total_ids[start : start + num]     # [0:0] = []
    return {'total_count': len(total_ids), 'features': paginated}

# Pretend the datastore has 5000 features.
total_ids = list(range(5000))

response = simulate_query(start=0, num=0, total_ids=total_ids)
print('simulate_query(start=0, num=0, total_ids=[0..4999]):')
print(f'  total_count: {response["total_count"]}')
print(f'  features:    {response["features"]!r}')
print()

assert response['total_count'] == 5000
assert response['features'] == []
print('CONFIRMED: num=0 → total_count=5000, features=[]  (HTTP 200, no 400).')
print()

# ── Step 3: contrast with num=-1 (correctly rejected) ────────────────────

rejected = get_int_arg('-1', default=100)
print(f'get_int_arg("-1", default=100) → {rejected!r}')
assert rejected == 'ABORT_400'
print('  → ABORT_400.  Negative correctly rejected.')
print()

# ── Summary ──────────────────────────────────────────────────────────────

print('CONFIRMED: GET /api/v0/features?num=0 returns HTTP 200 with empty features.')
print()
print('Root cause:')
print('  basehandlers.py:193  `if num < 0: self.abort(400, ...)`')
print('  The guard rejects negatives but has no positivity check: 0 passes.')
print()
print('Proposed fix:')
print('  After features_api.py:117, add:')
print('    if num == 0:')
print("        self.abort(400, msg='num must be a positive integer')")
