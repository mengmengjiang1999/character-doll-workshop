#!/usr/bin/env python3
"""Render local PMX mesh/UV data as four orthographic observation images.

Dependencies: numpy, Pillow. No Blender, network access, or model conversion.
Run from any working directory; defaults resolve relative to this repository.
This intentionally omits bones, physics, morphs, toon/sphere maps and lighting.
Transparent texels use a 0.5 alpha cutoff. Images show the default mesh pose,
not the in-game render, and model units are not doll measurements.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / (
    "projects/honkai-star-rail/march-7th-preservation-bjd-1-4/"
    "references/local/official-models"
)
DEFAULT_MODEL = REFERENCE_DIR / "extracted/星穹铁道—三月七/三月七 1.0.pmx"
VIEWS = (("front", 0), ("back", math.pi),
         ("left", -math.pi / 2), ("right", math.pi / 2))


class Reader:
    """Bounded reader for the PMX header, mesh, texture and material sections."""

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.encoding = "utf-8"

    def take(self, length: int) -> bytes:
        if length < 0 or self.offset + length > len(self.data):
            raise ValueError("Invalid or truncated PMX section")
        value = self.data[self.offset:self.offset + length]
        self.offset += length
        return value

    def unpack(self, fmt: str):
        values = struct.unpack("<" + fmt, self.take(struct.calcsize("<" + fmt)))
        return values[0] if len(values) == 1 else values

    def text(self) -> str:
        return self.take(self.unpack("i")).decode(self.encoding)

    def index(self, size: int) -> int:
        return self.unpack({1: "b", 2: "h", 4: "i"}[size])


def load_mesh(path: Path):
    reader = Reader(path.read_bytes())
    if reader.take(4) != b"PMX ":
        raise ValueError("Expected a PMX file")
    version = reader.unpack("f")
    if not (1.99 <= version <= 2.11):
        raise ValueError(f"Unsupported PMX version: {version}")
    header = list(reader.take(reader.unpack("B")))
    if len(header) != 8 or header[0] not in (0, 1):
        raise ValueError("Unsupported PMX header")
    if header[1] > 4 or any(size not in (1, 2, 4) for size in header[2:]):
        raise ValueError("Invalid PMX index or additional-UV size")
    reader.encoding = "utf-16-le" if header[0] == 0 else "utf-8"
    for _ in range(4):
        reader.text()

    vertices, uvs = [], []
    vertex_count = reader.unpack("i")
    if vertex_count <= 0 or vertex_count > len(reader.data) // 32:
        raise ValueError("Invalid PMX vertex count")
    bone_index_size = header[5]
    weights = {0: bone_index_size, 1: 2 * bone_index_size + 4,
               2: 4 * bone_index_size + 16, 3: 2 * bone_index_size + 40,
               4: 4 * bone_index_size + 16}
    for _ in range(vertex_count):
        vertices.append(reader.unpack("3f"))
        reader.take(12)  # normals; this renderer is unlit
        uvs.append(reader.unpack("2f"))
        reader.take(16 * header[1])
        weight_type = reader.unpack("B")
        if weight_type not in weights:
            raise ValueError(f"Unknown PMX deformation type: {weight_type}")
        reader.take(weights[weight_type] + 4)  # deformation data and edge scale
    vertices, uvs = np.asarray(vertices), np.asarray(uvs)
    if not np.isfinite(vertices).all() or not np.isfinite(uvs).all():
        raise ValueError("Non-finite vertex or UV data")

    index_count = reader.unpack("i")
    if index_count <= 0 or index_count % 3:
        raise ValueError("Invalid triangle index count")
    faces = np.frombuffer(reader.take(index_count * header[2]),
                          dtype={1: "u1", 2: "<u2", 4: "<u4"}[header[2]])
    faces = faces.reshape(-1, 3)
    if int(faces.max()) >= vertex_count:
        raise ValueError("Triangle references a missing vertex")

    textures = []
    for _ in range(reader.unpack("i")):
        relative = reader.text().replace("\\", "/")
        texture = (path.parent / relative).resolve()
        if not texture.is_relative_to(path.parent.resolve()):
            raise ValueError(f"Texture path leaves model directory: {relative}")
        with Image.open(texture) as image:
            textures.append(np.asarray(image.convert("RGBA")))

    materials, first = [], 0
    for _ in range(reader.unpack("i")):
        name = reader.text()
        reader.text()  # English name
        diffuse = np.asarray(reader.unpack("4f"))
        reader.take(12 + 4 + 12 + 1 + 16 + 4)  # specular/ambient/edge settings
        texture_index = reader.index(header[3])
        reader.index(header[3])  # sphere texture
        reader.take(1)  # sphere mode
        shared_toon = reader.unpack("B")
        reader.take(1 if shared_toon else header[3])
        reader.text()  # memo
        count = reader.unpack("i")
        if count < 0 or count % 3 or not (-1 <= texture_index < len(textures)):
            raise ValueError("Invalid material indices or texture")
        if not np.isfinite(diffuse).all():
            raise ValueError("Non-finite material color")
        last = first + count // 3
        materials.append((first, last, name, texture_index, diffuse))
        first = last
    if first != len(faces):
        raise ValueError("Material face counts do not cover the mesh")
    return vertices, uvs, faces, textures, materials


def render_view(mesh, angle, width, height, scale, hidden):
    vertices, uvs, faces, textures, materials = mesh
    cosine, sine = math.cos(angle), math.sin(angle)
    # Elementwise rotation avoids platform-specific BLAS floating-point warnings.
    xyz = np.column_stack((vertices[:, 0] * cosine + vertices[:, 2] * sine,
                           vertices[:, 1],
                           -vertices[:, 0] * sine + vertices[:, 2] * cosine))
    xy = np.column_stack((width / 2 + xyz[:, 0] * scale,
                          height - 55 - xyz[:, 1] * scale))
    depth = xyz[:, 2]
    canvas = np.full((height, width, 3), 247, dtype=np.uint8)
    zbuffer = np.full((height, width), np.inf)
    for first, last, name, texture_index, diffuse in materials:
        if name in hidden:
            continue
        texture = textures[texture_index] if texture_index >= 0 else None
        for indices in faces[first:last]:
            triangle = xy[indices]
            low = np.maximum(np.floor(triangle.min(axis=0)).astype(int), (0, 0))
            high = np.minimum(np.ceil(triangle.max(axis=0)).astype(int),
                              (width - 1, height - 1))
            if (high < low).any():
                continue
            a, b, c = triangle
            denominator = ((b[1] - c[1]) * (a[0] - c[0])
                           + (c[0] - b[0]) * (a[1] - c[1]))
            if abs(denominator) < 1e-8:
                continue
            x, y = np.meshgrid(np.arange(low[0], high[0] + 1) + 0.5,
                               np.arange(low[1], high[1] + 1) + 0.5)
            w0 = ((b[1] - c[1]) * (x - c[0])
                  + (c[0] - b[0]) * (y - c[1])) / denominator
            w1 = ((c[1] - a[1]) * (x - c[0])
                  + (a[0] - c[0]) * (y - c[1])) / denominator
            w2 = 1 - w0 - w1
            interpolated = (w0 * depth[indices[0]] + w1 * depth[indices[1]]
                            + w2 * depth[indices[2]])
            region = np.s_[low[1]:high[1] + 1, low[0]:high[0] + 1]
            z = zbuffer[region]
            mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (interpolated < z)
            if not mask.any():
                continue
            if texture is None:
                samples = np.full((*w0.shape, 4), 255, dtype=np.uint8)
            else:
                uv = (w0[..., None] * uvs[indices[0]]
                      + w1[..., None] * uvs[indices[1]]
                      + w2[..., None] * uvs[indices[2]])
                th, tw = texture.shape[:2]
                # PMX UVs can lie outside [0, 1]; preserve repeat addressing.
                tx = np.floor(uv[:, :, 0] * tw).astype(int) % tw
                ty = np.floor(uv[:, :, 1] * th).astype(int) % th
                samples = texture[ty, tx]
            mask &= samples[:, :, 3] / 255 * diffuse[3] > 0.5
            colors = np.clip(samples[:, :, :3] * diffuse[:3], 0, 255).astype(np.uint8)
            canvas[region][mask] = colors[mask]
            z[mask] = interpolated[mask]
    return Image.fromarray(canvas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL,
                        help="local PMX path; defaults to the downloaded March 7th model")
    parser.add_argument("--output", type=Path,
                        help="PNG output directory; default is a Git-ignored local directory")
    parser.add_argument("--label", default="March 7th | official PMX 1.0")
    parser.add_argument("--scale", type=float, default=46,
                        help="pixels per PMX unit, not mm (default: 46)")
    parser.add_argument("--width", type=int, default=760)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--hide-material", action="append", default=["表情"],
                        help="skip a named material; repeat as needed")
    args = parser.parse_args()
    if not math.isfinite(args.scale) or args.scale <= 0 or min(args.width, args.height) < 120:
        parser.error("scale must be finite and positive; image dimensions must be >= 120")
    model = args.model.resolve()
    if not model.is_file():
        parser.error(f"PMX not found: {model}; download the reference or pass --model")
    output = args.output or (REFERENCE_DIR / "rendered" if model == DEFAULT_MODEL.resolve()
                             else ROOT / ".private/reference-renders" / model.stem)
    output.mkdir(parents=True, exist_ok=True)
    try:
        mesh = load_mesh(model)
        board = Image.new("RGB", (4 * args.width, args.height), "white")
        for index, (name, angle) in enumerate(VIEWS):
            image = render_view(mesh, angle, args.width, args.height, args.scale,
                                set(args.hide_material))
            draw = ImageDraw.Draw(image)
            draw.text((20, 18), f"{args.label} | {name}", fill=(35, 40, 55))
            draw.text((20, args.height - 28),
                      "Local observation render / unlit texture / model units, not doll measurements",
                      fill=(55, 60, 70))
            image.save(output / f"{name}.png")
            board.paste(image, (args.width * index, 0))
            print(f"Rendered {name}", flush=True)
        board.save(output / "four-views.png")
    except (ValueError, OSError, UnicodeError) as error:
        parser.error(str(error))
    print(output.resolve() / "four-views.png")


if __name__ == "__main__":
    main()
