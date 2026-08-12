### Hi there, I'm Zhanyl 👋

I build **ML platforms** — the compute layer research teams train, evaluate, and
ship models on — and the **agent systems that operate them**.

- 🔭 **Currently building:** [`slurm-rca-bench`](https://github.com/Zhanyl-tech/slurm-rca-bench), the first public incident-diagnosis benchmark for HPC schedulers, and [`cluster-sre-agent`](https://github.com/Zhanyl-tech/cluster-sre-agent), a multi-agent diagnosis system scored against it.
- 🎓 **Education:** MS CS (Machine Learning) @ Georgia Tech · CQF (Quantitative Finance)
- ⚡ **Core stack:** Python · Go · PyTorch · CUDA · Slurm · Kubernetes · MCP
- 🖥 **Platform:** DCGM · MIG · NVLink/NVSwitch · InfiniBand/RoCE · Prometheus · Grafana
- 📈 **Focus:** GPU cluster infrastructure, inference optimization, and agentic operations

[Website](https://zhanyl-tech.github.io) · [LinkedIn](https://www.linkedin.com/in/za-engineering/) · [X](https://x.com/ZhanylAbd)

---

### 📊 Things I measured that turned out to be wrong

The repos below are ordinary. These are the parts worth reading — each one is a
belief I held, tested, and had to discard.

**Slurm priority weights barely matter.** Testing multifactor policy against a
real trace: enabling backfill moved CPU utilisation 72.2% → 83.6% and mean wait
1913.0 → 373.7 min. Sweeping the priority weights everyone tunes moved almost
nothing. The real lever was users' `--time` limits.
→ [slurm-scheduler-lab](https://github.com/Zhanyl-tech/slurm-scheduler-lab)

**The "storage stall halts scheduling" chain does not exist.** I built a
benchmark scenario around the folk model — filesystem → DB → slurmdbd →
slurmctld → scheduling halts. Then I measured it. Accounting goes dark and
scheduling keeps running: jobs submitted, started and completed normally
throughout, and `sinfo` never showed a stall. A second storage failure mode
(`StateSaveLocation` unwritable) fails loudly and instantly instead. The
scenario now ships documenting the refutation.
→ [slurm-rca-bench](https://github.com/Zhanyl-tech/slurm-rca-bench)

**A benchmark can be solved without reading any telemetry.** My own suite scored
0.290 for an agent that answers `db.mysql` to every question and looks at
nothing. Adding scenarios whose causes lie elsewhere cut it to 0.145, and a test
now fails the build if it climbs back. Publishing a score without that floor
tells the reader nothing.
→ [slurm-rca-bench](https://github.com/Zhanyl-tech/slurm-rca-bench#baselines--the-number-to-ask-for-first)

**`kubectl rollout restart` silently skips Slinky's compute nodes.** They're
owned by a `NodeSet` CRD, which `rollout restart` doesn't understand — so the
controller took a rotated auth key and `slurmd` kept the old one. My rotation
script reported success on a cluster that could not run a job.
→ [slinky-gitops](https://github.com/Zhanyl-tech/slinky-gitops#what-ci-caught)

---

### 🛠 Open source

Five tools covering the lifecycle of a GPU allocation, plus the benchmark and
agent built on top of them. Each is built on one rule: **never act on absent
evidence.**

| | |
|---|---|
| **[slurm-rca-bench](https://github.com/Zhanyl-tech/slurm-rca-bench)** | The first public incident-diagnosis benchmark for HPC schedulers. 10 scenarios, 2 deliberately undiagnosable, scored with partial credit against degenerate baselines. |
| **[cluster-sre-agent](https://github.com/Zhanyl-tech/cluster-sre-agent)** | Multi-agent cluster diagnosis, built as five ablatable configs so the dependency graph's contribution is measured rather than asserted. |
| **[slurm-scheduler-lab](https://github.com/Zhanyl-tech/slurm-scheduler-lab)** | Test Slurm priority and backfill policy against a real `sacct` trace before it reaches a live controller. |
| **[gpu-reaper](https://github.com/Zhanyl-tech/gpu-reaper)** | Reclaim idle GPU allocations, observe-by-default. A telemetry outage can never cancel a job. |
| **[ib-slurm-exporter](https://github.com/Zhanyl-tech/ib-slurm-exporter)** | Attribute InfiniBand/RoCE fabric counters to the Slurm job responsible — and refuse to attribute a shared device. |
| **[epilog-gpu-validator](https://github.com/Zhanyl-tech/epilog-gpu-validator)** | Drain a node for a *persistently* faulty GPU between jobs, never for a transient one. |
| **[slinky-gitops](https://github.com/Zhanyl-tech/slinky-gitops)** | Slurm on Kubernetes via SchedMD's Slinky, including the auth-key rotation nobody wants to test in production. |
| **[research-platform](https://github.com/Zhanyl-tech/research-platform)** | Point-in-time data semantics for quantitative research — as-of queries, feature lineage, and leakage detection. Production Python. |

More in progress — a multi-agent cluster diagnosis system and CUDA volatility
surface calibration. They go public as they get good enough to defend.

### ✍️ Writing

I publish at **[zhanyl-tech.github.io](https://zhanyl-tech.github.io)** — deep
dives on HPC and inference, plus shorter lab notes on whatever I'm currently
measuring.

- [Your Slurm priority weights matter less than your users' time limits](https://zhanyl-tech.github.io/experiments/2026-07-26-slurm-backfill-time-limits/)
- [LServe and SampleAttention: what sparse attention actually changes](https://zhanyl-tech.github.io/blog/2026-01-30-lserve-sampleattention-sparse-attention/)
- [How KV-cache paging works in vLLM](https://zhanyl-tech.github.io/blog/2026-01-15-kv-cache-paging-vllm/)

<sub>♟️ Chess and poker outside of work — both cheaper places to practise reasoning under uncertainty than production is.</sub>
