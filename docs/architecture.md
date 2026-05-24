# Architecture

GridFault Analyst is intentionally dependency-light.

## Frontend

The frontend is a static web application:

- `index.html` defines the dashboard layout and controls.
- `styles.css` contains the responsive interface styling.
- `app.js` performs live calculations and renders the single-line diagram state
  plus the time-current coordination chart.

The dashboard runs from the filesystem or from any simple static web server.

## Calculation Layer

The Python calculation layer lives in `src/` and mirrors the browser-side logic:

- `gridfault_calculations.py` owns input validation, fault-current equations,
  trip-time estimates, and result formatting.
- `gridfault_reports.py` exports a study to CSV.

Tests use the Python layer as the reference implementation for repeatable
verification.

## CI

GitHub Actions runs:

```bash
python -m unittest discover -s tests -v
```

on pushes and pull requests.
