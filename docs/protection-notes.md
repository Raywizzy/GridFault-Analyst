# Protection Notes

GridFault Analyst demonstrates the reasoning flow for a feeder fault study.

## Inputs

- Source line-to-line voltage
- Transformer MVA rating
- Transformer/source impedance percentage
- Feeder length
- Positive-sequence conductor resistance and reactance
- Fault location
- Fault type
- Relay pickup

## Protection Logic

The app estimates primary and backup clearing using a simplified IEC-style
inverse-time relationship:

```text
t = TMS * 0.14 / ((I / Is)^0.02 - 1)
```

where `I` is fault current and `Is` is pickup current.

## Limitations

The app is not a replacement for a certified protection study. Real projects
should include:

- Full positive, negative, and zero sequence impedances
- Source fault level from the utility
- CT ratios and relay curves
- Fuse manufacturer curves
- Breaker interrupting ratings
- Arc-flash study requirements
- Protection grading margins
