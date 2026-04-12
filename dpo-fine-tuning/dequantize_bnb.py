"""
Convert a bitsandbytes NF4-quantized safetensors model to plain float16.
Needed when merge_and_unload() was called on a still-quantized (QLoRA) model,
leaving the bnb quantization state tensors in the safetensors file.

Usage:
  python3 dequantize_bnb.py --input fluento-merged --output fluento-merged-fp16
"""

import argparse
import json
import os
import shutil
import numpy as np
from safetensors import safe_open
from safetensors.numpy import save_file


def dequant_absmax(absmax_uint8, nested_absmax, nested_quant_map, nested_offset):
    """
    Dequantize the double-quantized absmax values.
    absmax_uint8: uint8 array (N,) — indices into nested_quant_map
    nested_absmax: float32 array (N // nested_blocksize,) — per-group scales
    nested_quant_map: float32 array (256,) — 8-bit lookup table
    nested_offset: float scalar — offset added after lookup
    """
    nested_blocksize = 256
    absmax_float = nested_quant_map[absmax_uint8.astype(np.int32)]
    # Repeat each nested_absmax value for its block
    scales = np.repeat(nested_absmax, nested_blocksize)[: len(absmax_uint8)]
    absmax_float = absmax_float * scales + nested_offset
    return absmax_float


def dequant_nf4(packed_uint8, absmax_float, quant_map, shape, blocksize=64):
    """
    Dequantize packed NF4 weights.
    packed_uint8: uint8 array — 2 4-bit indices per byte (low nibble = first)
    absmax_float: float32 array (num_blocks,)
    quant_map: float32 array (16,) — NF4 lookup table
    shape: original weight shape tuple
    """
    flat = packed_uint8.reshape(-1)

    # Unpack nibbles: bitsandbytes packs as (first_val << 4) | second_val
    # so high nibble is the first element, low nibble is the second element
    high = ((flat >> 4) & 0x0F).astype(np.int32)
    low = (flat & 0x0F).astype(np.int32)

    # Interleave: [high[0], low[0], high[1], low[1], ...]
    indices = np.empty(len(flat) * 2, dtype=np.int32)
    indices[0::2] = high
    indices[1::2] = low

    n_elements = int(np.prod(shape))
    indices = indices[:n_elements]

    # Map each element to its block's absmax
    block_idx = np.arange(n_elements) // blocksize
    dequantized = quant_map[indices] * absmax_float[block_idx]

    return dequantized.reshape(shape).astype(np.float16)


def convert(input_dir, output_dir):
    safetensors_files = [f for f in os.listdir(input_dir) if f.endswith(".safetensors")]
    if not safetensors_files:
        raise FileNotFoundError(f"No .safetensors files found in {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Copy non-safetensors files (config, tokenizer, etc.)
    for fname in os.listdir(input_dir):
        if not fname.endswith(".safetensors"):
            src = os.path.join(input_dir, fname)
            dst = os.path.join(output_dir, fname)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"Copied: {fname}")

    for sf_file in safetensors_files:
        sf_path = os.path.join(input_dir, sf_file)
        print(f"\nProcessing {sf_file}...")

        with safe_open(sf_path, framework="numpy") as f:
            all_keys = list(f.keys())

        # Identify base weight keys (no bnb suffixes)
        bnb_suffixes = (".absmax", ".nested_absmax", ".nested_quant_map", ".quant_map", ".quant_state.bitsandbytes__nf4")
        base_keys = [k for k in all_keys if not any(k.endswith(s) for s in bnb_suffixes)]

        output_tensors = {}

        with safe_open(sf_path, framework="numpy") as f:
            for key in base_keys:
                tensor = f.get_tensor(key)
                qs_key = key + ".quant_state.bitsandbytes__nf4"

                if qs_key not in all_keys:
                    # Not quantized — keep as-is (cast to float16 if float)
                    if tensor.dtype in (np.float32, np.float64):
                        output_tensors[key] = tensor.astype(np.float16)
                    else:
                        output_tensors[key] = tensor
                    print(f"  {key}: kept ({tensor.dtype} {tensor.shape})")
                    continue

                # Parse quantization metadata
                qs_bytes = f.get_tensor(qs_key).tobytes()
                qs = json.loads(qs_bytes.decode("utf-8"))

                blocksize = qs["blocksize"]
                shape = tuple(qs["shape"])
                nested_offset = qs.get("nested_offset", 0.0)

                absmax_u8 = f.get_tensor(key + ".absmax")
                nested_absmax = f.get_tensor(key + ".nested_absmax")
                nested_quant_map = f.get_tensor(key + ".nested_quant_map")
                quant_map = f.get_tensor(key + ".quant_map")

                # Step 1: dequantize absmax
                absmax_float = dequant_absmax(absmax_u8, nested_absmax, nested_quant_map, nested_offset)

                # Step 2: dequantize weights
                dequantized = dequant_nf4(tensor, absmax_float, quant_map, shape, blocksize)

                output_tensors[key] = dequantized
                print(f"  {key}: dequantized {shape} → float16")

        out_path = os.path.join(output_dir, sf_file)
        save_file(output_tensors, out_path)
        print(f"\nSaved: {out_path}")

    print(f"\nDone. Model written to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="fluento-merged")
    parser.add_argument("--output", default="fluento-merged-fp16")
    args = parser.parse_args()
    convert(args.input, args.output)
