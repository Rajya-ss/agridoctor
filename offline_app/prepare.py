"""
prepare.py - fills the offline_app folder with everything the phone app needs.

Run from your project root (D:\adv\ten ans s), inside the .venv:
    python offline_app/prepare.py

It does five things:
  1. copies runs/model_run/model.onnx          -> offline_app/model.onnx
  2. copies runs/model_run/class_names.json    -> offline_app/labels.json
  3. copies your knowledge base (if found)     -> offline_app/kb.json
  4. downloads the ONNX Runtime Web files      -> offline_app/ort/   (needs internet once)
  5. writes files.json and stamps a new version into sw.js

Options:
    --model-dir runs/model_run
    --kb path/to/knowledge_base.json
    --ort-version 1.22.0
"""
import argparse
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORT_REQUIRED = ["ort.wasm.min.js", "ort-wasm-simd-threaded.wasm"]
ORT_OPTIONAL = ["ort-wasm-simd-threaded.mjs"]   # newer versions need it, older ones do not


def load_kb(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "diseases" in data and isinstance(data["diseases"], (list, dict)):
        data = data["diseases"]
    out = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                out[str(k)] = v
    elif isinstance(data, list):
        for v in data:
            if isinstance(v, dict):
                key = v.get("label") or v.get("class") or v.get("key") or v.get("id") or v.get("name")
                if key:
                    out[str(key)] = v
    return out


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgriDoctorPrepare/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"   could not download {url}: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default="runs/model_run")
    ap.add_argument("--kb", default=None)
    ap.add_argument("--ort-version", default="1.22.0")
    args = ap.parse_args()

    md = Path(args.model_dir)
    onnx, names = md / "model.onnx", md / "class_names.json"
    for p in (onnx, names):
        if not p.is_file():
            sys.exit(f"Missing {p}. Run this from the project root, or pass --model-dir.")
    if onnx.stat().st_size < 1_000_000:
        sys.exit(f"{onnx} is only {onnx.stat().st_size} bytes. The export is broken; export it again.")

    labels = json.loads(names.read_text(encoding="utf-8"))
    print(f"1. model.onnx ({onnx.stat().st_size / 1e6:.1f} MB), {len(labels)} class names")
    shutil.copyfile(onnx, HERE / "model.onnx")
    (HERE / "labels.json").write_text(json.dumps(labels, ensure_ascii=False), encoding="utf-8")

    # safety check: output size must equal number of labels
    try:
        import onnxruntime as ort
        s = ort.InferenceSession(str(onnx), providers=["CPUExecutionProvider"])
        n_out = s.get_outputs()[0].shape[-1]
        if n_out != len(labels):
            sys.exit(f"STOP: the model has {n_out} outputs but class_names.json has {len(labels)} names.")
        print(f"   check passed: model outputs {n_out} classes")
    except ImportError:
        print("   (onnxruntime not installed here, skipped the class-count check)")

    kb_path = Path(args.kb) if args.kb else next(
        (p for p in [Path("app/knowledge_base.json"), Path("knowledge_base.json"), md / "knowledge_base.json"] if p.is_file()), None)
    kb = {}
    if kb_path and kb_path.is_file():
        kb = load_kb(kb_path)
        print(f"2. knowledge base from {kb_path}: {len(kb)} entries")
    else:
        print("2. no knowledge_base.json found; the app will use its built-in general advice")
    (HERE / "kb.json").write_text(json.dumps(kb, ensure_ascii=False), encoding="utf-8")

    ort_dir = HERE / "ort"
    ort_dir.mkdir(exist_ok=True)
    base = f"https://cdn.jsdelivr.net/npm/onnxruntime-web@{args.ort_version}/dist/"
    print(f"3. downloading ONNX Runtime Web {args.ort_version} (one time, about 10 MB)")
    got = []
    for f in ORT_REQUIRED:
        if not download(base + f, ort_dir / f):
            sys.exit(f"STOP: required file {f} could not be downloaded. Check your internet, "
                     f"or try --ort-version 1.21.0")
        got.append(f)
    for f in ORT_OPTIONAL:
        if download(base + f, ort_dir / f):
            got.append(f)
    (HERE / "files.json").write_text(json.dumps({"ort": got}), encoding="utf-8")
    print("   saved:", ", ".join(got))

    sw = HERE / "sw.js"
    text = sw.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("const VERSION"):
            lines[i] = f'const VERSION = "{time.strftime("%Y%m%d%H%M%S")}";'
    sw.write_text("\n".join(lines), encoding="utf-8")
    print("4. service worker version updated")
    print("\nDone. Test it:  cd offline_app  then  python serve.py  then open http://localhost:8080")


if __name__ == "__main__":
    main()
