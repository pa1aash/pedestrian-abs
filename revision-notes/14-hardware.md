# S14 hardware

- CPU: Apple M1 (arm64)
- RAM: 8 GB
- OS: macOS 26.3.1 (Darwin 25.3.0)
- Python: 3.13.12
- numpy: 2.4.4
- scipy: 1.17.1
- shapely: 2.1.2

Source: `python -c "import platform; ..."` + `sysctl machdep.cpu.brand_string hw.memsize`, captured 2026-04-15 during S14 cProfile run.

The `00.5-reconstitution-final.md` header line ("Palaashs-MacBook-Air.local, Apple M-series (arm), Python 3.14") was produced on an older Python install; the S14 benchmarks in this revision use the 3.13.12 installed on the same machine as of 2026-04-15. Scaling numbers in `results_new/scaling_C{1,4}.csv` were produced under this Python 3.13 environment.
