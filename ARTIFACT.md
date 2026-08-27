# MICRO 2026 Artifact Evaluation Guide

The permanent archival DOI is reserved and will become publicly accessible
by the end of the artifact evaluation process.

## 1. What the artifact evaluates

This artifact provides a reduced-scale reproduction of the performance trend
in Fig. 18 of the paper *Loop-Decoupled Prefetcher for Linked Data
Structure*. It evaluates LDP and a no-prefetch baseline on:

- BFS, MST, and SSSP with the `cage10` and `sx-superuser` graph inputs;
- hash join probe with 1.28M build and probe tuples; and
- group-by with 1.28M input tuples.

The workflow contains eight tasks in total. Each restored simulation uses the
`O3_ARM_Neoverse_v2` CPU profile, DDR5-6400 memory, and a maximum of 10
million simulated instructions. The graph inputs may finish before reaching
the limit. The artifact does not evaluate the other prefetchers or the full
13-application suite used in the paper.

## 2. Components

- `src/mem/cache/prefetch/ldp.{cc,hh}`: LDP implementation.
- `configs/ldp/se.py`: ARM syscall-emulation configuration.
- `tasks/tasks.conf`: fixed task definitions.
- `workloads/`: AArch64 binaries and graph inputs.
- `scripts/run.py`: checkpoint, paired simulation, and collection workflow.
- `scripts/validate.py`: comparison with archived reference results.
- `expected/`: reference CSV and summary for the archived release.
- `checkpoints/`: supplied in the Docker image and Zenodo runtime bundle.

## 3. Resource requirements

No special CPU, GPU, FPGA, kernel module, performance counter, or proprietary
software is required. The host executes an ARM target through gem5, so the
host itself should be x86-64 Linux. Docker Engine is the only host dependency
for the recommended path.

The compressed image layers total approximately 845 MB. A clean public-image
run completed all eight tasks in 12 minutes 18 seconds on a GitHub-hosted
Ubuntu 24.04 runner with 4 vCPUs and 15 GB RAM. Four CPU cores are sufficient;
additional cores only increase the number of simulations that can run
concurrently.

## 4. Docker workflow

Pull the evaluated image by its immutable digest:

```bash
docker pull ghcr.io/forzacapybara/ldp-gem5-ae@sha256:86ad936a3d13d99b1e0c85df895c450a2ffa8746c72ee59610da1259b56aaf49
```

The human-readable release tag is `micro26-ae-v2`.

Run a single task as a functional check:

```bash
mkdir -p results
docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD/results:/results" \
  ghcr.io/forzacapybara/ldp-gem5-ae@sha256:86ad936a3d13d99b1e0c85df895c450a2ffa8746c72ee59610da1259b56aaf49 \
  python3 scripts/run.py \
    --gem5 /opt/ldp/bin/gem5.opt \
    --checkpoint-root /opt/ldp/checkpoints \
    --outdir /results --jobs 2 \
    --tasks graph_mst_queue_cg10
```

Run the complete eight-task subset:

```bash
rm -rf results
mkdir results
docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD/results:/results" \
  ghcr.io/forzacapybara/ldp-gem5-ae@sha256:86ad936a3d13d99b1e0c85df895c450a2ffa8746c72ee59610da1259b56aaf49 \
  python3 scripts/run.py \
    --gem5 /opt/ldp/bin/gem5.opt \
    --checkpoint-root /opt/ldp/checkpoints \
    --outdir /results --jobs 4
```

Validate the complete result:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD/results:/results" \
  ghcr.io/forzacapybara/ldp-gem5-ae@sha256:86ad936a3d13d99b1e0c85df895c450a2ffa8746c72ee59610da1259b56aaf49 \
  python3 scripts/validate.py \
    --actual /results/analysis/speedup.csv \
    --output-root /results
```

Success is reported as `VALIDATION PASSED: 8 task(s)`. The validation requires:

1. all eight task rows are present;
2. no-prefetch and LDP instruction counts differ by no more than 10
   instructions per task (gem5 may cross the limit by a few instructions);
3. LDP is faster than no-prefetch for every task; and
4. reproduced speedups are within 5% of the archived reference.

`--user "$(id -u):$(id -g)"` maps the container process to the invoking
POSIX user, so files created through the bind mount remain writable and
host-owned. On Windows Docker Desktop, place `results` in a shared local
directory and grant the current user write access before running the command.

## 5. Native workflow

Install the build dependencies and build gem5:

```bash
sudo apt-get update
sudo apt-get install -y build-essential scons python3.10-dev \
  zlib1g-dev m4 pkg-config
source sourceme
PYTHON_CONFIG=python3.10-config \
CCFLAGS_EXTRA='-include stdint.h' \
scons build/ARM_LDP/gem5.opt -j"$(nproc)"
```

Without packaged checkpoints, the runner first uses `AtomicSimpleCPU` until
the workload's built-in checkpoint instruction and exits after the first
checkpoint. It then restores both configurations:

```bash
python3 scripts/run.py --jobs 4
python3 scripts/validate.py
```

With the Zenodo checkpoint bundle:

```bash
python3 scripts/run.py \
  --checkpoint-root /path/to/checkpoints \
  --outdir "$PWD/results" --jobs 4
python3 scripts/validate.py \
  --actual "$PWD/results/analysis/speedup.csv" \
  --output-root "$PWD/results"
```

## 6. Output interpretation

For each task, `scripts/run.py` records the actual gem5 command in
`<configuration>/command.txt` and writes:

- `stats_nopf_restored.txt`: no-prefetch statistics;
- `stats_ldp_restored.txt`: LDP statistics;
- `<task>_<configuration>.log`: simulator output;
- `analysis/speedup.csv`: task-level simulated time and speedup; and
- `analysis/summary.txt`: application and task-weighted overall geometric
  means.

Speedup for task \(i\) is:

\[
S_i =
\frac{\mathrm{simSeconds}_{\mathrm{no\mbox{-}prefetch},i}}
     {\mathrm{simSeconds}_{\mathrm{LDP},i}}.
\]

The reported overall speedup is the geometric mean of the eight task
speedups. It is not the 13-application 1.97x result reported in the paper.

## 7. Loop-decoupling mechanism ablation

The optional mechanism experiment retains the no-prefetch and full-LDP
configurations above and adds `ldp_no_loop_restored`. This third configuration
changes only `--ldp-link-detection-enable` from `true` to `false`; the
checkpoint, CPU, cache hierarchy, other LDP controls, and instruction window
remain unchanged.

Run all three configurations:

```bash
rm -rf results
mkdir results
docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD/results:/results" \
  ghcr.io/forzacapybara/ldp-gem5-ae:micro26-ae-v2 \
  python3 scripts/run.py \
    --gem5 /opt/ldp/bin/gem5.opt \
    --checkpoint-root /opt/ldp/checkpoints \
    --outdir /results --jobs 4 --mechanism-ablation
python3 scripts/validate_mechanism.py \
  --actual results/analysis/mechanism_summary.csv
```

The clean reference run takes about 14 minutes on a four-vCPU GitHub-hosted
runner. It generates task-level raw counters in `mechanism.csv`,
application-level values in `mechanism_summary.csv`, and the three-panel
`mechanism.svg`.

For each configuration, coverage and timeliness are fixed as:

\[
\mathrm{Coverage} =
\frac{\mathrm{pfUseful}}
     {\mathrm{pfUseful}+\mathrm{demandMshrMisses}},
\qquad
\mathrm{Timeliness} =
\frac{\mathrm{pfUseful}}
     {\mathrm{pfUseful}+\mathrm{demandMshrHitsAtPf}}.
\]

A zero timeliness denominator means that the configuration produced no demand
access affected by a prefetch and is reported as zero. Speedup remains
`simSeconds(noPF) / simSeconds(variant)`. The raw gem5 stats are retained so
reviewers can audit every derived value.

Across the eight tasks, enabling loop decoupling increases mean coverage from
12.7% to 49.1%, mean timeliness from 32.7% to 70.9%, and task-weighted
geometric-mean speedup from 1.087x to 2.254x. BFS, MST, SSSP, and HJ-P show
the same direction; GB is unchanged in this compact interval.

## 8. Customization

`scripts/run.py --help` lists the supported controls. Reviewers may select
tasks, change parallelism, use another output root, or use the alternative
`O3_ARM_Neoverse` profile. Results from modified profiles or instruction
limits are exploratory and should not be compared against the archived
reference CSV.

## 9. Troubleshooting

- `gem5 binary not found`: use the Docker image or complete the native build.
- `Missing checkpoint(s)`: verify that `--checkpoint-root` contains one
  `cpt.*` directory with `m5.cpt` under each selected task.
- `VALIDATION FAILED`: inspect the listed task, paired stats files, and
  per-configuration logs. Do not reuse checkpoints generated with a different
  memory/CPU profile.
- Docker output permission errors: retain the documented `--user` and
  `HOME=/tmp` options and verify that the host directory is writable. As a
  POSIX fallback, run `chmod a+rwx results`; on Docker Desktop, use a shared
  local directory rather than a restricted or network-mounted path.

Report evaluation problems through the GitHub issue tracker and include the
image digest, host OS, command, and failing task log.
