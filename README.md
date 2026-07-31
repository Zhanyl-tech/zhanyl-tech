### Hi there, I'm Zhanyl 👋

I'm a **Senior Cluster SRE**. I write tools for GPU clusters that operators
actually want running — the scheduling, health, and observability gaps you only
notice once a cluster is full and something is quietly wasting it.

- 🔭 **Currently building:** open-source tooling for Slurm and Kubernetes GPU
  clusters — scheduler policy testing, GPU health validation, and per-job fabric
  observability.
- 🎓 **Education:** MS CS (Machine Learning) @ Georgia Tech · CQF (Quantitative Finance).
- ⚡ **Core stack:** Go · Python · Slurm · Kubernetes · Docker · NVML/nvidia-smi.
- 📈 **Focus:** GPU-cluster reliability, and never acting on absent evidence —
  every tool below is built to fail safe when it can't see clearly.

[Website](https://zhanyl-tech.github.io) · [LinkedIn](https://www.linkedin.com/in/za-engineering/) · [X / Twitter](https://x.com/ZhanylAbd)

---

### 🛠 Open source

A set, not scattered weekend projects. Together they cover the lifecycle of a
GPU allocation — decide the policy, catch waste during a job, attribute fabric
problems to the job causing them, validate the hardware between jobs, and run
the whole thing on Kubernetes.

**[slurm-scheduler-lab](https://github.com/Zhanyl-tech/slurm-scheduler-lab)** —
test Slurm priority and backfill policy against a real job trace **before** it
reaches a live controller. Implements `priority/multifactor` and EASY backfill,
reads `PriorityWeight*` straight from a `slurm.conf`, and replays `sacct` traces.
I built it to answer a question I couldn't safely test in production — and the
answer turned out not to be the weights:

```
backfill OFF                          backfill ON
  cpu utilization      72.2 %           cpu utilization      83.6 %
  mean wait          1913.0 min         mean wait           373.7 min
```

**[gpu-reaper](https://github.com/Zhanyl-tech/gpu-reaper)** — find and reclaim
idle GPU allocations, observe-by-default. The whole design is one rule: killing a
healthy job is worse than letting a wasted one run, so a collector outage can
never cancel anything and a kill requires a history of warnings first.

**[ib-slurm-exporter](https://github.com/Zhanyl-tech/ib-slurm-exporter)** —
attribute InfiniBand/RoCE fabric counters to the Slurm job responsible, and
refuse to attribute a device two jobs share. A correlation the usual exporters
don't draw.

**[epilog-gpu-validator](https://github.com/Zhanyl-tech/epilog-gpu-validator)** —
drain a node for a *persistently* faulty GPU between jobs, and never for a
transient one. The companion to gpu-reaper: waste during a job vs. hardware
between them.

**[slinky-gitops](https://github.com/Zhanyl-tech/slinky-gitops)** — run Slurm on
Kubernetes via SchedMD's Slinky, declaratively, including the auth-key rotation
nobody wants to test in production. Documents honestly what does and doesn't work
on the current release.

### ✍️ Writing

I publish at **[zhanyl-tech.github.io](https://zhanyl-tech.github.io)** — deep
dives on HPC and inference, plus shorter lab notes on whatever I'm currently
measuring.

- [Your Slurm priority weights matter less than your users' time limits](https://zhanyl-tech.github.io/experiments/2026-07-26-slurm-backfill-time-limits/)
- [LServe and SampleAttention: what sparse attention actually changes](https://zhanyl-tech.github.io/blog/2026-01-30-lserve-sampleattention-sparse-attention/)
- [How KV-cache paging works in vLLM](https://zhanyl-tech.github.io/blog/2026-01-15-kv-cache-paging-vllm/)

<sub>♟️ Chess and poker outside of work — both cheaper places to practise reasoning under uncertainty than production is.</sub>
