#!/usr/bin/env python3
"""Generate an original, simplified quatrefoil fitting sample. Millimetres.

No official model geometry is used. Python standard library only for meshes;
optional --preview uses matplotlib. The solids share vertices at every join.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'projects/honkai-star-rail/march-7th-hunt-bandai-sitting-plush/models'


def mesh_from_loops(loops, caps):
    n = len(loops[0])
    vertices = [p for loop in loops for p in loop]
    faces = []
    for layer in range(len(loops) - 1):
        for i in range(n):
            j = (i + 1) % n
            a, b, c, d = layer*n+i, layer*n+j, (layer+1)*n+j, (layer+1)*n+i
            faces.extend([(a, b, c), (a, c, d)])
    if caps:
        for layer, reverse in [(0, True), (len(loops)-1, False)]:
            center = len(vertices)
            vertices.append((0, 0, loops[layer][0][2]))
            for i in range(n):
                a, b = layer*n+i, layer*n+(i+1)%n
                faces.append((center, b, a) if reverse else (center, a, b))
    else:
        # Inner wall ends at bottom; close bottom annulus to outer wall.
        for i in range(n):
            j = (i+1) % n
            a, b, c, d = (len(loops)-1)*n+i, (len(loops)-1)*n+j, j, i
            faces.extend([(a, b, c), (a, c, d)])
    return vertices, faces


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def inspect(vertices, faces):
    from collections import Counter
    edges, directions = Counter(), Counter()
    volume = 0.0
    for face in faces:
        a, b, c = [vertices[i] for i in face]
        ab = tuple(b[i]-a[i] for i in range(3))
        ac = tuple(c[i]-a[i] for i in range(3))
        normal = cross(ab, ac)
        assert sum(v*v for v in normal) > 1e-14, 'Degenerate triangle'
        volume += sum(a[i]*cross(b, c)[i] for i in range(3))/6
        for u, v in zip(face, face[1:]+face[:1]):
            edges[tuple(sorted((u, v)))] += 1
            directions[(u, v)] += 1
    assert all(count == 2 for count in edges.values()), 'Open or non-manifold edge'
    assert all(directions[(v, u)] == count for (u, v), count in directions.items()), 'Inconsistent orientation'
    assert volume > 0, 'Non-positive volume'
    dimensions = [round(max(p[i] for p in vertices)-min(p[i] for p in vertices), 4) for i in range(3)]
    return {'vertices': len(vertices), 'triangles': len(faces), 'closed_oriented_edges': True,
            'volume_mm3': round(volume, 4), 'dimensions_mm': dimensions,
            'physical_fit': 'NOT TESTED'}


def write_stl(path, vertices, faces):
    with path.open('w') as f:
        f.write('solid original_fitting_sample_mm\n')
        for ids in faces:
            a, b, c = [vertices[i] for i in ids]
            normal = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
            length = math.sqrt(sum(v*v for v in normal))
            f.write('  facet normal ' + ' '.join(f'{v/length:.8g}' for v in normal) + '\n    outer loop\n')
            for p in (a, b, c):
                f.write('      vertex ' + ' '.join(f'{v:.8g}' for v in p) + '\n')
            f.write('    endloop\n  endfacet\n')
        f.write('endsolid original_fitting_sample_mm\n')


def write_scad(path, vertices, faces):
    # OpenSCAD polyhedron winding is clockwise from outside; STL is opposite.
    scad_faces = [list(reversed(face)) for face in faces]
    path.write_text('// Original fitting sample; mm; edit via tools/generate_accessories.py\n'
                    '// No official character mesh used. Physical fit NOT TESTED.\n'
                    + 'polyhedron(points=' + json.dumps(vertices) + ', faces='
                    + json.dumps(scad_faces) + ', convexity=10);\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--width', type=float, default=24.0, help='design trial width in mm, not measured from doll')
    parser.add_argument('--height', type=float, default=2.2)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    if not (12 <= args.width <= 60 and 1.2 <= args.height <= 5):
        parser.error('trial width must be 12..60 mm; height 1.2..5 mm')
    OUT.mkdir(parents=True, exist_ok=True)
    n = 128
    angles = [2*math.pi*i/n for i in range(n)]
    outline = [(args.width/2)*(0.78+0.22*math.cos(4*t)) for t in angles]
    loops = []
    # Bottom chamfer -> side -> upper lip -> recessed face.
    for scale, z in [(0.96, 0), (1, .18*args.height), (1, .82*args.height),
                     (.96, args.height), (.72, args.height), (.72, .65*args.height)]:
        loops.append([(r*scale*math.cos(t), r*scale*math.sin(t), z) for r,t in zip(outline,angles)])
    flower = mesh_from_loops(loops, True)
    # Separate closed oval loop for sewing onto a ribbon; not fused with ornament.
    loop_profiles = [(8.7,3.7,0), (9,4,.3), (9,4,1.3), (8.7,3.7,1.6),
                     (6.3,1.9,1.6), (6,1.6,1.3), (6,1.6,.3), (6.3,1.9,0)]
    backing_scale = args.width/24
    backing = mesh_from_loops([[(rx*backing_scale*math.cos(t),ry*backing_scale*math.sin(t),z) for t in angles]
                              for rx,ry,z in loop_profiles], False)
    report = {'status': 'DRAFT - geometry checked, no print or fit test',
              'parameters': {'ornament_width_mm': args.width, 'ornament_height_mm': args.height,
                             'status': 'design trial values, not doll measurements'}, 'models': {}}
    for name, mesh in [('hunt-quatrefoil-v0.1-draft',flower), ('sew-on-loop-v0.1-draft',backing)]:
        report['models'][name] = inspect(*mesh)
        write_stl(OUT/(name+'.stl'), *mesh)
        write_scad(OUT/(name+'.scad'), *mesh)
    (OUT/'geometry-checks.json').write_text(json.dumps(report, indent=2)+'\n')
    if args.preview:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.colors import to_rgb
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        fig = plt.figure(figsize=(11,5), facecolor='#f6f3ed')
        for idx, (title, mesh, color) in enumerate([
                ('Hunt quatrefoil | 24 mm trial' if args.width == 24 else f'Hunt quatrefoil | {args.width:g} mm trial',flower,'#dbb865'),
                (f'Separate sew-on loop | {18*backing_scale:g} x {8*backing_scale:g} mm',backing,'#83a7b2')],1):
            ax = fig.add_subplot(1,2,idx,projection='3d')
            v,f = mesh
            colors = []
            for tri in f:
                a,b,c = [v[j] for j in tri]
                normal = cross(tuple(b[k]-a[k] for k in range(3)), tuple(c[k]-a[k] for k in range(3)))
                length = math.sqrt(sum(x*x for x in normal))
                lighting = .55 + .45*max(0, (normal[0]*.25-normal[1]*.35+normal[2]*.9)/length)
                colors.append(tuple(channel*lighting for channel in to_rgb(color)))
            ax.add_collection3d(Poly3DCollection([[v[j] for j in tri] for tri in f], facecolors=colors, edgecolors='none'))
            bound=max(max(abs(p[0]),abs(p[1])) for p in v)*1.12
            ax.set(xlim=(-bound,bound),ylim=(-bound,bound),zlim=(0,4),xlabel='mm',ylabel='mm',title=title)
            ax.set_zticks([0,2,4])
            ax.set_box_aspect((2*bound,2*bound,8)); ax.view_init(elev=62,azim=-60)
        fig.suptitle('DRAFT v0.1 | Original simplified geometry | NOT print / fit tested',fontsize=13)
        fig.tight_layout(); fig.savefig(OUT/'accessories-preview.png',dpi=160); plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
