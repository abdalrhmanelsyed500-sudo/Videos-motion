# Stage 2 measurements — 2026-10-28

Reproduce from the repository root after installing the headless harness:

```sh
(cd pixel_pirates/tools/godot_node && npm ci)
python3 iron_atlas/tools/benchmark_stage2.py
```

Raw output for this run: [`stage2_benchmark.json`](stage2_benchmark.json).
The environment was Linux x86_64, Node **v22.22.3**, Godot **4.7.2**
web template in the Node WASM harness; the sandbox exposed two vCPUs on an
Intel Xeon 2.60 GHz host. This is headless: no renderer, audio, GPU or browser
frame time is included. Results are one run on a shared sandbox, not a hardware
requirement or a promise of consistent performance.

| Measurement | Result | Method / caveat |
|---|---:|---|
| World generation, mean | **13.19 ms** | 10 seeds, 200 districts, includes generator's validation |
| World generation, median / range | **12.17 ms / 11.73–17.98 ms** | Same 10 samples |
| Invalid generated worlds | **0 / 10** | Separate land graph + ID validation after each sample |
| Simulation cost, mean / median | **7.98 / 5.68 ms per day** | 200 day ticks including scheduled week/month work; 29 formations at end |
| Simulation cost, p95 / maximum | **27.29 / 31.68 ms per day** | Same sample; some days include AI and weekly systems |
| Peak process RSS | **245,048 KiB ≈ 239.3 MiB** | Linux `getrusage(RUSAGE_CHILDREN)` for the entire Node+WASM child, not incremental world RAM |
| Initial serialized state | **159,124 bytes** | JSON encoding, not resident memory |
| Save after 200 days | **749,708 bytes** | Readable JSON plus exact binary Variant copy |
| Godot static-memory monitor | **unavailable** | Returned 0 in this WASM build; no per-world heap claim |

The screenshot run used a separate Chromium/SwiftShader renderer; it was not
benchmarked. **FPS, GPU use, native-desktop load time, 200-region rendering
cost, and performance on modest physical hardware were not measured.**
