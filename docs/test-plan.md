# Test Plan

## Automated Tests

Run:

```bash
python3 -m unittest discover -s tests -v
```

Coverage includes:

- Reference fault-current case
- Fault-type multiplier behavior
- Fault location effect on current
- Invalid input rejection
- Inverse-time trip behavior
- CSV report export

## Manual Browser Checks

Run:

```bash
python3 -m http.server 5174
```

Then open:

```text
http://127.0.0.1:5174
```

Check:

- Dashboard loads without console errors
- Fault location slider moves the marker
- Fault current changes when fault type changes
- Time-current chart is visible
- Layout remains usable on mobile width
