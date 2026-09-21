# Troubleshooting

## No sensor
Check power → connector → interface/bus → device discovery → packet stream. Do not replace missing data with a plausible value.

## Noisy signal
Check sensor contact, motion, placement and sampling rate. Inspect quality metrics before interpreting features.

## Serial disconnect
Record disconnect, preserve the gap, reconnect, then verify sequence counters before resuming.

## APK build failure
Verify JDK 17, Android SDK 34, Gradle wrapper permissions and platform/build-tools installation.
