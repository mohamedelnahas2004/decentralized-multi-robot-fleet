#!/usr/bin/env python3
"""Print bounding box, center and size of an STL file (binary or ASCII).

Uses trimesh or numpy-stl when installed, otherwise a built-in numpy parser,
so it works with no extra dependencies.

  ros2 run fleet_description inspect_mesh.py meshes/lidar.stl
  python3 scripts/inspect_mesh.py meshes/zed.stl --scan-height 0.0207
"""
import argparse
import struct
import sys

import numpy as np


def _load_with_trimesh(path):
    import trimesh
    mesh = trimesh.load(path, force='mesh')
    return np.asarray(mesh.vertices, dtype=float)


def _load_with_numpy_stl(path):
    from stl import mesh
    return np.asarray(mesh.Mesh.from_file(path).vectors, dtype=float).reshape(-1, 3)


def _load_builtin(path):
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) >= 84:
        n_tri = struct.unpack('<I', data[80:84])[0]
        if len(data) == 84 + 50 * n_tri:  # binary STL
            dtype = np.dtype([('normal', '<f4', 3), ('v', '<f4', (3, 3)), ('attr', '<u2')])
            tris = np.frombuffer(data, dtype=dtype, count=n_tri, offset=84)
            return tris['v'].reshape(-1, 3).astype(float)
    verts = []  # ASCII STL
    for line in data.decode('utf-8', errors='ignore').splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] == 'vertex':
            verts.append([float(p) for p in parts[1:]])
    if not verts:
        raise ValueError('not a valid binary or ASCII STL file')
    return np.asarray(verts, dtype=float)


def load_vertices(path):
    for loader in (_load_with_trimesh, _load_with_numpy_stl):
        try:
            return loader(path)
        except ImportError:
            continue
    return _load_builtin(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('stl', help='path to an STL file')
    parser.add_argument('--scale', type=float, default=1.0,
                        help='multiply vertices by this factor (e.g. 0.001 for mm files)')
    parser.add_argument('--scan-height', type=float, default=0.0,
                        help='lidar only: scan plane height above the mesh bottom [m]')
    args = parser.parse_args()

    v = load_vertices(args.stl) * args.scale
    lo, hi = v.min(axis=0), v.max(axis=0)
    size, center = hi - lo, (lo + hi) / 2.0

    print(f'file     : {args.stl}')
    print(f'vertices : {len(v)}')
    print(f'min  xyz : {lo[0]: .5f} {lo[1]: .5f} {lo[2]: .5f}')
    print(f'max  xyz : {hi[0]: .5f} {hi[1]: .5f} {hi[2]: .5f}')
    print(f'size xyz : {size[0]: .5f} {size[1]: .5f} {size[2]: .5f}')
    print(f'center   : {center[0]: .5f} {center[1]: .5f} {center[2]: .5f}')
    print()
    print('Visual <origin> that centers XY on the link axis and puts the mesh bottom at '
          f'z = -{args.scan_height:g}:')
    print(f'  xyz="{-center[0]:.5f} {-center[1]:.5f} {-lo[2] - args.scan_height:.5f}"')
    print('Visual <origin> that centers the mesh completely on the link origin:')
    print(f'  xyz="{-center[0]:.5f} {-center[1]:.5f} {-center[2]:.5f}"')
    if size.max() > 5.0:
        print('\nWARNING: largest dimension > 5 -> file is probably in mm; '
              'use scale="0.001 0.001 0.001" or re-export in meters.', file=sys.stderr)


if __name__ == '__main__':
    main()
