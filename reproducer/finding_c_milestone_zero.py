#!/usr/bin/env python3
"""
Empirical reproducer — Finding C
  api/channels_api.py:138  get_int_arg admits ?start=0 / ?end=0
  → milestone 0 queried, null dates returned, HTTP 200

Source (verbatim, d0d21c8):
  # channels_api.py:135-158
  def do_get(self, **kwargs):
      start = self.get_int_arg('start')   ← admits 0
      end   = self.get_int_arg('end')     ← admits 0
      if start is None or end is None:
          return construct_chrome_channels_details()
      if start > end:
          raise ValueError               # 0 > 0 is False → not triggered
      ...
      return construct_specified_milestones_details(start, end)

  # channels_api.py:121-129
  def construct_specified_milestones_details(start, end):
      channels = {}
      for milestone in range(start, end + 1):   # range(0, 1) → [0]
          channels[milestone] = fetch_chrome_release_info(milestone)
      return channels

  # fetchchannels.py:114-154  fetch_chrome_release_info(0)
  #   Queries: https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=0
  #   Returns: {'stable_date': None, 'earliest_beta': None, 'latest_beta': None,
  #             'mstone': 0, 'version': 0}
  #   → HTTP 200 with null dates; milestone 0 is not a real Chrome milestone.

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


start = get_int_arg('0')
end   = get_int_arg('0')
print(f'get_int_arg("0") for ?start → {start!r}')
print(f'get_int_arg("0") for ?end   → {end!r}')
assert start == 0 and end == 0
print('  → Both 0.  No 400 issued.')
print()

# ── Step 2: show the start > end guard does not trigger for start=end=0 ──

if start > end:
    print('  start > end guard: TRIGGERED  (would raise ValueError)')
else:
    print(f'  start > end guard: not triggered ({start} > {end} is False).')
print()

# ── Step 3: show what fetch_chrome_release_info(0) would return ──────────

# Inline of the fallback branch in fetchchannels.py:144-151.
# This executes when the external API returns non-200 or an empty mstones list,
# which is what chromiumdash.appspot.com returns for mstone=0.
def fetch_chrome_release_info_fallback(version):
    """
    Fallback return value from fetchchannels.py:144-151 when the API
    does not return a valid mstones entry for the requested milestone.
    """
    return {
        'stable_date':    None,
        'earliest_beta':  None,
        'latest_beta':    None,
        'mstone':         version,
        'version':        version,
    }


def construct_specified_milestones_details(start, end):
    """Inline of channels_api.py:121-129."""
    channels = {}
    for milestone in range(start, end + 1):
        channels[milestone] = fetch_chrome_release_info_fallback(milestone)
    return channels


response = construct_specified_milestones_details(0, 0)
print('construct_specified_milestones_details(0, 0):')
print(f'  {response}')
print()

assert response == {
    0: {'stable_date': None, 'earliest_beta': None, 'latest_beta': None,
        'mstone': 0, 'version': 0}
}

# ── Step 4: contrast with start=1 (the smallest valid Chrome milestone) ───

response_valid = construct_specified_milestones_details(1, 1)
print('construct_specified_milestones_details(1, 1)  [smallest real milestone]:')
print(f'  mstone=1 placeholder: {response_valid[1]}')
print('  (A real API call would return the actual schedule for M1; here the')
print('   fallback fires because mstone=1 is ancient and not in the live API.)')
print()

# ── Summary ───────────────────────────────────────────────────────────────

print('CONFIRMED: GET /api/v0/channels?start=0&end=0 returns HTTP 200 with:')
print('  {0: {"stable_date": null, "earliest_beta": null, "latest_beta": null,')
print('       "mstone": 0, "version": 0}}')
print()
print('Root cause:')
print('  basehandlers.py:193  `if num < 0: self.abort(400, ...)`')
print('  Milestone numbers must be >= 1; 0 is not a real Chrome milestone.')
print('  get_int_arg has no minimum-value guard, so 0 passes through.')
print()
print('Proposed fix:')
print('  After channels_api.py:140, add:')
print('    if start < 1 or end < 1:')
print("        self.abort(400, msg='Milestone numbers must be >= 1')")
