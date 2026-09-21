# Testing Guide

Run existing tests plus V8.4 integration tests. Required coverage includes sensor failure, packet corruption, missing data, baseline/longitudinal behavior, fusion, disease registry, database migrations, security, patient isolation, imaging gates, report generation, demo mode, API boundary and Android builds.

Critical invariants:
- Patient A cannot access Patient B.
- DEMO-001 cannot access DEMO-002.
- DEMO_DATA cannot silently become real data.
- Unavailable imaging models return explicit unavailable/insufficient state.
