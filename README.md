# LDP-gem5

This repository contains the MICRO 2026 artifact for the Loop-Decoupled
Prefetcher (LDP). It provides a compact ARM syscall-emulation gem5, the LDP
implementation, fixed AArch64 workloads and inputs, and an automated workflow
for comparing LDP against a no-prefetch baseline.

LDP targets linked-data-structure traversals whose inner pointer-chasing
accesses are interleaved with outer-loop accesses. It uses loop decoupling,
bidirectional pattern reconstruction, and cross-loop prefetching to recognize
these accesses and start future traversals early.

## Artifact scope

The artifact evaluates five applications (BFS, MST, SSSP, hash join probe,
and group-by) in eight task/input combinations. It reproduces the direction
of the central result in Fig. 18:
LDP improves simulated execution time over the no-prefetch baseline on this
representative subset.

This reduced workflow does **not** reproduce all 13 paper applications, the
other prefetchers in Fig. 18, or the paper's 1.97x full-suite geometric mean.
Restored simulations use the `O3_ARM_Neoverse_v2` profile and execute at most
10 million instructions. See [ARTIFACT.md](ARTIFACT.md) for the exact scope,
commands, expected outputs, and limitations.

## Recommended: Docker

The published image includes the prebuilt simulator and compatible
checkpoints:

```bash
mkdir -p results
docker run --rm \
  -v "$PWD/results:/results" \
  ghcr.io/forzacapybara/ldp-gem5-ae:micro26-ae-v1 \
  python3 scripts/run.py \
    --gem5 /opt/ldp/bin/gem5.opt \
    --checkpoint-root /opt/ldp/checkpoints \
    --outdir /results --jobs 4
```

Validate the reproduced results:

```bash
docker run --rm \
  -v "$PWD/results:/results" \
  ghcr.io/forzacapybara/ldp-gem5-ae:micro26-ae-v1 \
  python3 scripts/validate.py --actual /results/analysis/speedup.csv \
    --output-root /results
```

The permanent archival DOI is reserved and will become publicly accessible
by the end of the artifact evaluation process.

The immutable digest will be recorded after the anonymized image is built and
validated.

## Native build

The tested native environment is Ubuntu 24.04 x86-64 with Python 3.10:

```bash
sudo apt-get update
sudo apt-get install -y build-essential scons python3.10-dev \
  zlib1g-dev m4 pkg-config
source sourceme
PYTHON_CONFIG=python3.10-config \
CCFLAGS_EXTRA='-include stdint.h' \
scons build/ARM_LDP/gem5.opt -j"$(nproc)"
```

Generate checkpoints when none are supplied, run all eight tasks, and collect
results:

```bash
python3 scripts/run.py --jobs 4
python3 scripts/validate.py
```

To keep packaged checkpoints read-only and write outputs elsewhere:

```bash
python3 scripts/run.py \
  --checkpoint-root /path/to/checkpoints \
  --outdir /path/to/results --jobs 4
```

Run selected tasks or only recollect existing outputs:

```bash
python3 scripts/run.py --tasks graph_bfs_queue_ss database_hj_m
python3 scripts/run.py --collect-only
```

## Outputs

- `m5out/<task>/stats_nopf_restored.txt`
- `m5out/<task>/stats_ldp_restored.txt`
- `m5out/analysis/speedup.csv`
- `m5out/analysis/summary.txt`

For task \(i\), speedup is
`simSeconds(no-prefetch) / simSeconds(LDP)`. The overall value is the
task-weighted geometric mean across all eight tasks. For applications with two
graph inputs, the runner also reports an application-level geometric mean.

The source code is distributed under the BSD 3-Clause license. Workload and
dataset provenance and licenses are documented in [THIRD_PARTY.md](THIRD_PARTY.md).
