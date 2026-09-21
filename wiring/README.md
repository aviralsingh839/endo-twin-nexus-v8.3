# Wiring guide

This directory is the source-of-truth location for verified wiring diagrams.

## Rule
Do not document an exact Arduino pin assignment unless the exact breakout/module variant has been identified and checked against its manufacturer documentation. Common I2C sensors can share SDA/SCL; analog sensors require an appropriate ADC input; temperature probes require the correct pull-up and bus arrangement.

The exact board variant must be recorded in the wiring record before assembly.
