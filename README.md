### Zhanyl — GPU cluster scheduling and fleet health, on Slurm and Kubernetes

<!-- OWNER: the full name and a job title are already public elsewhere, but neither was added here without your confirmation. "Zhanyl Abdybaeva" is in every linked repo's LICENSE and on the website (hugo.yaml title and author, content/about.md). The site's subtitle is "Senior HPC & ML Infrastructure Engineer", and about.md says "a senior cluster engineer in platform engineering at a quantitative hedge fund". Decide whether this heading should match the site. -->

<!-- OWNER: almost every line below describes work that exists only as uncommitted changes on the improve/2026-09 branch of the repo it links to. On 2026-09-26 all eleven linked repos and zhanyl-tech.github.io had them, and each one's HEAD was still its origin/main. Commit and merge all of them before publishing this README, or most linked repos will contradict it. `python scripts/check_profile.py claims` (without --local) reads each repo's default branch, so it fails until they are merged. -->

I build the systems that allocate scarce, expensive, heterogeneous compute —
and the benchmarks that check whether they actually work.

Each repo below has a status: **built** (code and tests exist), **partial**
(part of it is built and the rest is marked planned), or **planned** (nothing
exists yet). Each number says how it was produced. None of them comes from a
GPU or a production cluster. Where a live control plane was involved, the line
says which one.

[Website](https://zhanyl-tech.github.io) · [LinkedIn](https://www.linkedin.com/in/za-engineering/) · [X](https://x.com/ZhanylAbd)

---

### Scheduling evaluation: Slurm and Kubernetes, same trace

| repo | status | what it is |
|---|---|---|
| **[k8s-gpu-scheduler-lab](https://github.com/Zhanyl-tech/k8s-gpu-scheduler-lab)** | partial | Kubernetes GPU schedulers on identical traces. The control plane and kube-scheduler are real (kind), and the GPU nodes are kwok objects with no hardware. **Built:** K0 (default kube-scheduler) and four degenerate baselines; a Phase 2 harness with repeats and a bootstrap screen, not yet run on a cluster. **Planned:** Kueue, Volcano, NVIDIA's Volcano bin-packing, KAI with DRA. |
| **[slurm-scheduler-lab](https://github.com/Zhanyl-tech/slurm-scheduler-lab)** | built · model only | A discrete-event model of Slurm's multifactor priority (Fair Tree and classic fairshare), `sched/backfill`-style conservative backfill and EASY, and QOS/partition preemption. It reads a `slurm.conf` and replays synthetic, `sacct` or k8s-lab traces. Its semantics come from the Slurm docs and source; nothing has been replayed against a live `slurmctld`. |

The two labs share a fleet format and a structural fragmentation definition,
pinned by a common golden test vector. slurm-scheduler-lab can replay a k8s-lab
trace through the Slurm model (the S0 control, model only). No S0-versus-K0
comparison has been published.

### GPU fleet health

These tools share one rule: **never act on absent evidence.**

| repo | status | what it is |
|---|---|---|
| **[gpu-reaper](https://github.com/Zhanyl-tech/gpu-reaper)** | built · not yet run on a cluster | Finds Slurm GPU allocations doing no work, and drains or cancels them only if you enable it. It only observes by default. Missing, stale or unreadable telemetry is never read as idleness. A gap between observations longer than `max_sample_gap`, which with the defaults means any failed collection cycle, restarts the escalation from the first alert. It cancels only after a drain that was executed and confirmed at least one window earlier. It reads `nvidia-smi` or dcgm-exporter; the DCGM source is untested against a real exporter. Tested against a simulator, fake Slurm and NVIDIA binaries, and synthetic dcgm-exporter pages. |
| **[epilog-gpu-validator](https://github.com/Zhanyl-tech/epilog-gpu-validator)** | built · not validated on hardware | A Slurm Epilog check of the GPUs a job just used. It drains a node only on findings it classes as fatal or degraded, and only with `--enforce`. A GPU query that fails or times out keeps the node in service; `nvidia-smi`'s documented hardware-fault exits (8, 10, 14, 15) count as evidence. It keeps no history, so "persistent" is a judgement about the fault class, not an observation over time. Exercised against simulated `nvidia-smi` output and fake binaries. |
| **[ib-slurm-exporter](https://github.com/Zhanyl-tech/ib-slurm-exporter)** | built · synthetic sysfs only | Attributes InfiniBand/RoCE port counters to the Slurm job using the HCA, and withholds the job label on any port it can see is shared. In its default mode, kernel RDMA users (NFS/RDMA, Lustre o2ib, IPoIB) are invisible to it, so it cannot see them sharing a port. Handles Slurm 26.05's SLUID-keyed cgroup paths. Tested against synthetic `/sys`, `/proc` and cgroup trees; not yet run on IB hardware or a 26.05 node. |
| **[slinky-gitops](https://github.com/Zhanyl-tech/slinky-gitops)** | partial | Slurm 26.05 on Kubernetes through Slinky v1.2 on kind, with CI. On Slinky v1.2 the auth-key rotation does not currently take. In three kind CI runs (commits `8e742be` to `c51903a`) the rotation exited non-zero instead of reporting success, and the cluster ran a job afterwards; the run logs, which would show the rollback, were not re-read. The September 2026 rewrite hashes the key in every slurmd pod and in slurmctld, exits 3 after a verified rollback, and has a CI step assert that exit. So far the script has run only in offline tests against a fake `kubectl`, and the new CI step has not run at all. One NodeSet, no GPUs. The "GitOps" is still planned: no Argo CD yet. |

### Agentic operations, read-only first

| repo | status | what it is |
|---|---|---|
| **[slurm-rca-bench](https://github.com/Zhanyl-tech/slurm-rca-bench)** | partial | An incident-diagnosis benchmark for the Slurm control plane. 10 scenarios are designed and 6 are runnable. 2 have causal chains measured on a live Slurm 25.11.4 control plane in Docker; the 0.2.0 injection and heal fixes have not been re-run on that cluster. Grading uses a closed vocabulary with no LLM judge, against degenerate baselines. The leaderboard is empty. |
| **[slurm-mcp](https://github.com/Zhanyl-tech/slurm-mcp)** | built · fixtures only | A read-only MCP server for Slurm state. Its allowlist is enforced in code and tested with 70 adversarial argv, and it exposes three tools with progressive disclosure. Not yet run against a real cluster. |
| **[cluster-ops-skills](https://github.com/Zhanyl-tech/cluster-ops-skills)** | built · not scored | 11 runbooks (10 for Slurm, 1 for Slinky) packaged as Agent Skills, each with a mandatory "what not to conclude" section, checked by a validator. Whether they help an agent is unmeasured. |
| **[cluster-sre-agent](https://github.com/Zhanyl-tech/cluster-sre-agent)** | partial | A five-configuration ablation, specified before any results, of whether an explicit dependency graph helps an LLM diagnose Slurm incidents. **Built:** the graph (12 edges, 4 measured on the benchmark's cluster) and a read-only command guard. **Planned:** agent configurations A–E and any MCP server. No accuracy has been measured. |

Other: **[research-platform](https://github.com/Zhanyl-tech/research-platform)** (partial), a point-in-time (bitemporal)
data layer for quantitative research. It serves as-of queries over an
append-only DuckDB store and is checked with `mypy --strict`. It is Phase 1 of
6; feature lineage and leakage detection are planned.

---

### Things I measured that turned out to be wrong

Each of these is a belief I held, tested, and had to discard. Three of them
correct what an earlier version of this profile said.

**"Slurm priority weights barely matter; users' `--time` limits are the real
lever."** My own simulator contradicts both halves.
Backfill does matter: on a synthetic 300-job trace (seed 5), enabling it moved
CPU utilisation 72.3% → 83.0% and mean wait 1896.7 → 396.1 min, and across
seeds 0–9 it cut mean wait 2.2x-5.7x. Not every weight is flat either.
Sweeping each one from 0 to 100,000 changed mean wait by at most 1.26x for age,
but by 1.13x-1.84x for fairshare, 1.50x-2.81x for QOS and 2.15x-3.87x for job
size. And exact limits did not help waiting. Setting every limit equal to its
job's runtime, with nothing else changed, raised CPU utilisation on 7/10 seeds
but also raised mean wait on 9/10. That matches the studies Tsafrir
[reviews](https://dants.github.io/papers/Keynote10JSSPP.pdf) (JSSPP 2010),
Mu'alem & Feitelson (IEEE TPDS 2001) among them. He argues their padding model,
proportional to runtime, leaks runtime information to the scheduler. My padding
is proportional to runtime too, so this says nothing yet about real users'
limits.
<sub>Reference model, synthetic traces, no live controller: 16 nodes × 8 CPU /
2 GPU, conservative backfill, Fair Tree. `schedlab --compare-backfill --jobs 300 --seed 5`,
and the seed loops in [`scripts/reproduce_scheduler_claims.py`](scripts/reproduce_scheduler_claims.py). Run 2026-09-26.</sub>
→ [slurm-scheduler-lab](https://github.com/Zhanyl-tech/slurm-scheduler-lab#time-limits-what-accurate-requests-buy-measured)
<!-- OWNER: these numbers come from slurm-scheduler-lab's improve/2026-09 working tree (base c02b52f plus uncommitted changes: conservative backfill and Fair Tree became the defaults). They were re-derived on 2026-09-26 by `scripts/check_profile.py reproduce` against that working tree, three times (started 23:24, 23:28 and 23:32 CDT, identical output; the last run passed every reproduce check), after the lab's model changed again at 22:55–23:05 (model.py, cli.py, metrics.py, preempt.py and simulate.py under src/schedlab). The previous version of this paragraph quoted 89.9% / 442.5 min, 2.1x, 1.20x, 1.83x, 1.52x-2.63x, 2.16x-3.92x and utilisation up on 9/10 from the lab's earlier working tree; by 23:32 the lab's README had moved to the numbers above. Its main branch still prints the old 72.2% → 83.6% / 1913.0 → 373.7 min. Merge that branch before publishing this README (see the merge note at the top), re-run the reproduce step if the model changes again, then set `slurm-scheduler-lab` under `[refs]` in claims.toml to the merge commit, so the reproduce job re-derives these numbers at the commit they came from as well as on main. -->

**"A GPU fragmentation percentage is one number."** On one kind + kwok run
(a real Kubernetes control plane, simulated GPU nodes, n=1), the
largest-first baseline scored **0.0%** fragmentation under a queue-relative
definition and **55.6%** under a queue-independent one, on the same data. So a
fragmentation figure without its definition cannot be reproduced. That includes
the "34% at KubeCon EU 2026" figure the lab was started to test, whose source I
could not verify: I found it only in a
[third-party blog post](https://devops.gheware.com/blog/posts/top-kubernetes-integrations-ai-gpu-acceleration-2026.html)
that names no talk, and
[NVIDIA's own write-up](https://developer.nvidia.com/blog/practical-tips-for-preventing-gpu-fragmentation-for-volcano-scheduler/)
of its Volcano bin-packing reports node counts (18 → 214 nodes with all four
GPUs free), not a percentage. The same configuration, run twice, varied more than most of
the differences between schedulers, so no absolute number from that run can be
quoted yet.
<sub>`results/results.json` in k8s-gpu-scheduler-lab: Run 2, 800 jobs / 1201 pods on a 140-GPU heterogeneous fleet, Phase 1 harness.</sub>
→ [k8s-gpu-scheduler-lab](https://github.com/Zhanyl-tech/k8s-gpu-scheduler-lab#metrics)

**"`kubectl rollout restart` reaches every pod that holds the key."** On
Slinky, compute pods are owned by a `NodeSet` CRD. `rollout restart`'s
documented resource types are deployments, daemonsets and statefulsets
([kubectl docs](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/)).
So slurmctld adopted a rotated auth key while slurmd kept the old one, and my
rotation script reported success on a cluster that could not run a job. Fixing
that exposed a harder failure: a newly created slurmd pod still mounted the
*previous* key. In three later CI runs on kind (commits `8e742be` to
`c51903a`) the rotation exited non-zero instead of reporting success, and the
cluster ran a job afterwards. The September 2026 rewrite hashes the key in
every slurmd pod and in slurmctld, exits 3 after a verified rollback, and has
CI assert that exit. It has so far run only in offline tests against a fake
`kubectl`; the kind job has not run it yet. The cause is still a hypothesis (the kubelet's
cache of an immutable Secret) that has not been reproduced in isolation. An
upstream issue is drafted but not filed.
→ [slinky-gitops](https://github.com/Zhanyl-tech/slinky-gitops#what-ci-caught)

**"A stalled accounting database halts Slurm scheduling."** I built a
benchmark scenario around that folk chain, then measured it. I froze the
database (`docker pause` on MariaDB) for about 15 minutes on a Slurm 25.11.4
control plane in Docker Compose with one compute node, and scheduling did not
halt. `sacct` blocked with no error. slurmctld's DBD agent queue reached 6 and
flushed on recovery. Both jobs submitted during the stall ran to completion,
though job start latency rose to tens of seconds. The
[slurm.conf docs](https://slurm.schedmd.com/slurm.conf.html#OPT_MaxDBDMsgs)
say slurmctld queues these messages while slurmdbd is unreachable, with a limit
of at least 10000, so this run never came near saturation. Making
`StateSaveLocation` unwritable behaved the opposite way: the one submission
attempted during the fault was rejected at once with an I/O error, and no
backlog built up. The database stall was probed in full in one emulated run,
and a second run confirmed the queue growth; the unwritable state was one run.
Two jobs were submitted during the database stall and one during the
unwritable state, and a `StateSaveLocation` *stall* is untested. The
scenario also needed a second correction. It still gave full credit to a
shared filesystem that the emulated cluster does not have, and it now credits
the frozen database.
→ [slurm-rca-bench](https://github.com/Zhanyl-tech/slurm-rca-bench#the-first-finding-is-about-the-benchmark-itself)

**"Adding scenarios fixed my benchmark's degenerate floor."** It did, and then
two correct fixes undid it. At 5 scenarios, answering `db.mysql` to every task
scored 0.290 while reading nothing. Adding scenarios whose causes lie elsewhere
cut that to 0.145 over 10. Then S01's full credit moved to the only layer its
injection touches, and four scenarios whose injections cannot produce their
ground truth were blocked and left the denominator. Over the 6 runnable
scenarios the same constant answer now scores 0.333, above the suite's own 0.25
threshold. The test that enforces the threshold is a strict expected failure
until new runnable scenarios fix the suite. Publishing a score without that
floor tells the reader nothing.
<sub>`slurm-rca baselines`, run 2026-09-26: 0.333 over 6 runnable scenarios (0.200 with `--include-blocked`). 0.290 (its S01–S05) and 0.145 recomputed at commit 469ea76, before the corrections.</sub>
→ [slurm-rca-bench](https://github.com/Zhanyl-tech/slurm-rca-bench#baselines--the-number-to-ask-for-first)

---

<p align="center">
  <img src="./assets/architecture.svg" alt="Four bands. Scheduling evaluation: slurm-scheduler-lab (built, reference model) and k8s-gpu-scheduler-lab (partial: K0 and four degenerate baselines built; Kueue, Volcano and KAI planned), sharing a trace, a fleet and fragmentation definition C. GPU fleet health: gpu-reaper, epilog-gpu-validator and ib-slurm-exporter built but not yet run on a cluster or hardware; slinky-gitops partial, with a rotation that fails safe. The Slurm control plane as measured in slurm-rca-bench (Slurm 25.11.4 in Docker): shared filesystem to accounting database is inferred; the database halting slurmdbd is measured; slurmdbd to slurmctld only degrades, measured; slurmctld to scheduling halts, documented; an unwritable StateSaveLocation rejected the one submission tried, measured once. Agentic operations: slurm-rca-bench partial, slurm-mcp and cluster-ops-skills built, cluster-sre-agent partial with its agent loop planned. On control-plane edges, solid means measured and dashed means documented or inferred; the dotted link between the two labs means shared inputs, not a measurement." width="100%">
</p>

---

### Writing

I publish at **[zhanyl-tech.github.io](https://zhanyl-tech.github.io)**: deep
dives on HPC and inference, plus shorter lab notes on whatever I'm currently
measuring.

- [Slurm Backfill vs. Priority Weights on a Synthetic Workload: What One Seed Showed, and What Twenty Did Not](https://zhanyl-tech.github.io/experiments/2026-07-26-slurm-backfill-time-limits/) (July 2026, **corrected** September 2026). The original claimed that priority weights barely matter. That came from one synthetic seed, and across 20 seeds it does not hold, on the original simulator code as well as the current one. See the first finding above.
  <!-- OWNER: two things are still outstanding. (1) The correction is in zhanyl-tech.github.io's uncommitted improve/2026-09 changes; on 2026-09-26 the live page still carried the old title, "Your Slurm Priority Weights Matter Less Than Your Users' Time Limits". Deploy it before publishing this entry. (2) cluster-ops-skills' backfill-not-running runbook still has a section headed "Why time limits come first", with its figures pinned to slurm-scheduler-lab c02b52f, while the September version of that simulator has exact limits raising mean wait on 9 of 10 seeds (the first finding above). Remove this note once both are done. -->
- [LServe and SampleAttention: what sparse attention actually changes](https://zhanyl-tech.github.io/blog/2026-01-30-lserve-sampleattention-sparse-attention/)
- [How KV-cache paging works in vLLM](https://zhanyl-tech.github.io/blog/2026-01-15-kv-cache-paging-vllm/)

<!-- OWNER: the previous README promised "a CUDA port of a volatility surface calibration"; the site's gpu-volatility-surface milestones (Jul and Sep 2026) have passed. Add it back, as planned, only if it still is. -->

### Background

- **Education:** MS CS (Machine Learning) @ Georgia Tech · CQF (Quantitative Finance) · NVIDIA NCP-AIO <!-- OWNER: add the MS completion year or "(in progress, exp. YYYY)", and a public verification link for NCP-AIO if one exists. Neither is recorded in the workspace. -->
- **Core stack:** Python, Go, PyTorch, CUDA, Kubernetes, Slurm
- **Platform:** NVIDIA BCM · Run:ai · DCGM · MIG · NVLink/NVSwitch · DOCA/BlueField · InfiniBand · Prometheus
- **Focus:** scheduling and resource allocation across Slurm and Kubernetes, GPU cluster reliability, inference infrastructure, and agentic operations

<sub>Chess and poker outside of work — both cheaper places to practise reasoning under uncertainty than production is.</sub>
