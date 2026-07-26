### Hi there, I'm Zhanyl 👋

I am a **Senior Quant Research Engineer** bridging the gap between High-Performance Computing and Alpha Generation.

- 🔭 **Currently building:** Autonomous DeFAI trading agents (LLM + RL) on distributed infrastructure.
- 🎓 **Education:** MS CS (Machine Learning) @ Georgia Tech | CQF (Quantitative Finance).
- ⚡ **Core Stack:** Python, C++, PyTorch, CUDA, Slurm, AWS ParallelCluster, Kubernetes, Docker.
- 📈 **Focus:** HFT Infrastructure, Market Microstructure, and AI-driven Trading Strategies.

[Website](https://zhanyl-tech.github.io) | [LinkedIn](https://www.linkedin.com/in/za-engineering/) | [X / Twitter](https://x.com/ZhanylAbd)

---

### 🛠 Open source

**[slurm-scheduler-lab](https://github.com/Zhanyl-tech/slurm-scheduler-lab)** — test Slurm priority and backfill policy against a job trace before it reaches a live controller.

Implements `priority/multifactor` and EASY backfill, reads `PriorityWeight*` straight from a `slurm.conf`, and replays real `sacct` traces. I built it to answer a question I couldn't safely test in production — and the answer turned out not to be the weights:

```
backfill OFF                          backfill ON
  cpu utilization      72.2 %           cpu utilization      83.6 %
  mean wait          1913.0 min         mean wait           373.7 min
```

More in progress — agentic inference infrastructure, 128-GPU distributed training, and CUDA volatility surface calibration. They go public as they get good enough to defend.

### ✍️ Writing

I publish at **[zhanyl-tech.github.io](https://zhanyl-tech.github.io)** — deep dives on inference optimization and HPC, plus shorter lab notes on whatever I'm currently measuring.

- [Your Slurm priority weights matter less than your users' time limits](https://zhanyl-tech.github.io/experiments/2026-07-26-slurm-backfill-time-limits/)
- [LServe and SampleAttention: what sparse attention actually changes](https://zhanyl-tech.github.io/blog/2026-01-30-lserve-sampleattention-sparse-attention/)
- [How KV-cache paging works in vLLM](https://zhanyl-tech.github.io/blog/2026-01-15-kv-cache-paging-vllm/)

<sub>♟️ Chess and poker outside of work — both cheaper places to practise reasoning under uncertainty than production is.</sub>
