# Last-Mile Percentile

[Open Last-Mile Percentile](https://coolcode.ca/lastmilepercentile/) to compare a download or upload speed with a distribution of voluntary tests on a particular Canadian network.

<!-- coolcode:guide -->
Choose a month, city and network, then enter your speed in Mbps. Each comparison shows the two published boundaries around your result and the number of tests behind them.
<!-- /coolcode:guide -->

The initial September 2026 edition places 100 Mbps between P25 and P50 for TELUS AS852 in Langley, BC (6,331 download tests) and between P50 and P75 for Eastlink AS11260 in Halifax, NS (4,898). Upload and download sample counts are independent. Your number stays in browser memory. An optional visitor-started NDT7 speed test fills the comparison speed. M-Lab publishes the test address and measurements. Manual comparisons work offline after the monthly file loads.

The bundled Apache-2.0 M-Lab client and worker files in `web/ndt/` are from [ndt7-js commit 1b6da4c](https://github.com/m-lab/ndt7-js/tree/1b6da4cd7743fba0b3bbff5d78815abcc95c87d1). Run the test only after reading the consent text.

## Reading the measurements

M-Lab publishes speed estimates at P1, P5, P10, P25, P50, P75, P90, P95 and P99. Below P1 and above P99 are open-ended bands. Equal thresholds are labelled together. The classifier compares full source precision, while chart labels round to two decimal places. Hover over a number to see its original value. A sample describes voluntary tests, can include repeat testers and cannot guarantee a plan speed or an exact personal percentile. IP-based city assignment is approximate.

## Data and operation

The extract includes Canadian province/city/ASN groups with a known city and network and at least 100 valid tests in one direction. The page keeps the three most recent months for which both directions have been published. The date and source Parquet link are shown on the page. Missing groups do not meet the selection or are absent upstream. Network labels follow M-Lab.

[Monthly Stats source](https://www.measurementlab.net/kb/monthly-stats-dataset/) · [Public file manifest](https://storage.googleapis.com/mlab-sandbox-iqb-us-central1/manifest/v0/manifest.json)

A weekly GitHub Actions check downloads the six source files, verifies their SHA-256 checksums against the manifest, builds and tests the refreshed site, and publishes it to Pages. A failed check leaves the previous deployment live. The repository includes a reproducible initial edition for offline builds. To recreate the current edition locally, install Python 3.12 and pyarrow 19.0.1, then run the following commands.

```sh
python scripts/refresh.py
node --test tests/*.test.mjs
python -m unittest discover -s tests
python scripts/build.py
python -m http.server --directory dist 8000
```

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
