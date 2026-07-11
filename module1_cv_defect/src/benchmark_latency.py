"""Rigorous single-image inference latency benchmark for the paper.

Reports batch=1 latency with a proper protocol: a warm-up phase (the
first calls include one-time CUDA/graph setup and must be discarded),
then many timed runs, reporting mean / std / median / p95. Measured for
three deployment-relevant configurations so the paper can state exactly
what the number refers to instead of a bare "~13 ms":
  - PyTorch on GPU
  - PyTorch on CPU
  - ONNX Runtime on CPU  (the actual offline edge-deployment target)

Usage:
    python src/benchmark_latency.py
"""
import argparse
import time

import numpy as np
import torch

from model import build_model


def summarize(times_ms):
    a = np.array(times_ms)
    return {"mean": a.mean(), "std": a.std(), "median": np.median(a), "p95": np.percentile(a, 95)}


def bench_torch(model, device, n_warmup, n_runs):
    model.eval()
    x = torch.randn(1, 3, 224, 224, device=device)
    with torch.no_grad():
        for _ in range(n_warmup):
            model(x)
            if device.type == "cuda":
                torch.cuda.synchronize()
        times = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            model(x)
            if device.type == "cuda":
                torch.cuda.synchronize()
            times.append((time.perf_counter() - t0) * 1000)
    return summarize(times)


def bench_onnx(onnx_path, n_warmup, n_runs):
    import onnxruntime as ort
    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    name = sess.get_inputs()[0].name
    x = np.random.randn(1, 3, 224, 224).astype(np.float32)
    for _ in range(n_warmup):
        sess.run(None, {name: x})
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        sess.run(None, {name: x})
        times.append((time.perf_counter() - t0) * 1000)
    return summarize(times)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="models/casting_mobilenetv2_proper.pt")
    ap.add_argument("--onnx", default="models/casting_mobilenetv2.onnx")
    ap.add_argument("--warmup", type=int, default=30)
    ap.add_argument("--runs", type=int, default=300)
    args = ap.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu")
    model = build_model(num_classes=len(ckpt["classes"]), freeze_base=True)
    model.load_state_dict(ckpt["model_state_dict"])

    print(f"Protocol: batch=1, {args.warmup} warm-up runs discarded, {args.runs} timed runs\n")

    if torch.cuda.is_available():
        gpu = bench_torch(model.cuda(), torch.device("cuda"), args.warmup, args.runs)
        print(f"PyTorch GPU ({torch.cuda.get_device_name(0)}):")
        print(f"  mean={gpu['mean']:.2f}ms  std={gpu['std']:.2f}  median={gpu['median']:.2f}  p95={gpu['p95']:.2f}")

    cpu = bench_torch(model.cpu(), torch.device("cpu"), args.warmup, args.runs)
    print("PyTorch CPU:")
    print(f"  mean={cpu['mean']:.2f}ms  std={cpu['std']:.2f}  median={cpu['median']:.2f}  p95={cpu['p95']:.2f}")

    try:
        onnx = bench_onnx(args.onnx, args.warmup, args.runs)
        print("ONNX Runtime CPU (edge-deployment target):")
        print(f"  mean={onnx['mean']:.2f}ms  std={onnx['std']:.2f}  median={onnx['median']:.2f}  p95={onnx['p95']:.2f}")
    except Exception as e:
        print(f"ONNX benchmark skipped: {e}")


if __name__ == "__main__":
    main()
