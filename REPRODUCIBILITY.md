# Reproducing the Arrow Lake-H Three-Tier Scheduling Benchmarks

## Quick start (TL;DR)

On the reference machine, after a fresh boot:

```bash
./scripts/pin_system.sh            # one-time per boot
./scripts/prep_session.sh          # one-time per session
./scripts/pass_A_stream_1t.sh      
./scripts/pass_B_stream_full.sh    
systemd-inhibit --what=sleep:idle:handle-lid-switch --who=arrowlake-bench --why="NPB 1-thread" \
  ./scripts/pass_C_npb_1t.sh       
systemd-inhibit --what=sleep:idle:handle-lid-switch --who=arrowlake-bench --why="NPB full-tier" \
  ./scripts/pass_D_npb_full.sh     
./scripts/aggregate.py             
```

##  Hardware

| Component | Specification |
|-----------|---------------|
| Machine | ASUS ROG G16 (2025 model) |
| CPU | Intel Core Ultra 9 285H (Arrow Lake-H, 6 P + 8 E + 2 LP E = 16 cores, no SMT) |
| Memory | 32 GB LPDDR5x-8400 (dual channel, as shipped) |
| Storage | NVMe SSD (as shipped) |
| Power | AC adapter; charge to 100% before starting |

## 2. Software

| Component | Version used | Install |
|-----------|-------------|---------|
| OS | Fedora 43 Workstation | Fresh install |
| Kernel | 6.17.1-300.fc43.x86_64 | Default Fedora 43 |
| Compiler | gcc 15.2.1 | `dnf install -y gcc gcc-gfortran` |
| perf | kernel-tools matching 6.17.1 | `dnf install -y kernel-tools` |
| msr module | (in-tree) | `sudo modprobe msr` (required for §6 only) |
| Python | 3.13 | `dnf install -y python3 python3-pandas python3-matplotlib python3-numpy` |
| Other CLI | `taskset`, `lscpu`, `lstopo`, `turbostat`, `dmidecode`, `systemd-inhibit`, `rdmsr` (msr-tools) | `dnf install -y util-linux hwloc kernel-tools dmidecode systemd msr-tools` |


The benchmark source trees are externally maintained and are not committed to this repository

```bash
cd /path/to/ArrowLakeHBenchmarking
mkdir -p benchmarks && cd benchmarks


mkdir -p STREAM && cd STREAM
wget http://www.cs.virginia.edu/stream/FTP/Code/stream.c
wget http://www.cs.virginia.edu/stream/FTP/Code/mysecond.c
# Makefile is not distributed; a minimal one is shown in this repo's
# paper discussion. See the build commands below.
cd ..

# NPB-OMP-C — a C+OpenMP port of the NAS Parallel Benchmarks.
# Use the widely-cited port at https://github.com/benchmark-subsetting/NPB3.0-omp-C
# or equivalent (the published results were measured against that port
# with the stock config/make.def). Clone, then `make <kernel> CLASS=B`.
git clone https://github.com/benchmark-subsetting/NPB3.0-omp-C NPB-OMP-C
```

## Build
### STREAM (McCalpin)

```bash
cd benchmarks/STREAM
gcc -O3 -fopenmp -mcmodel=medium -DSTREAM_ARRAY_SIZE=12000000 \
    stream.c mysecond.c -o stream_omp
./stream_omp   # smoke test, expects ~24 GB/s on a single P-core
```



### NPB-OMP-C (NAS Parallel Benchmarks, OpenMP-C port)

```bash
cd benchmarks/NPB-OMP-C
# Default cflags:
#   CFLAGS = -O3 -fopenmp -mcmodel=medium
# Build the class-B kernels we use:
make EP CLASS=B
make CG CLASS=B
make IS CLASS=B
make MG CLASS=B
```


# run after boot prior to benchmarks
```bash
./scripts/pin_system.sh
```

The companion `scripts/unpin_system.sh` reverts these changes after the session.

### per-session prep (`scripts/prep_session.sh`)

```bash
./scripts/prep_session.sh
```

## 5. Running the Phase 2 measurement set


```bash
cd /path/to/ArrowLakeHBenchmarking

# One-time
./scripts/pin_system.sh
./scripts/prep_session.sh


./scripts/pass_A_stream_1t.sh


./scripts/pass_B_stream_full.sh


systemd-inhibit --what=sleep:idle:handle-lid-switch --who=arrowlake-bench \
  --why="NPB 1-thread sweep" ./scripts/pass_C_npb_1t.sh


systemd-inhibit --what=sleep:idle:handle-lid-switch --who=arrowlake-bench \
  --why="NPB full-tier sweep" ./scripts/pass_D_npb_full.sh


./scripts/aggregate.py
```


