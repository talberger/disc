"""
image coloring by back-projection: color every pixel of the segmented object in the
photo with the colors of the mesh vertices it corresponds to. The exact inverse of
color_mesh_from_knn.py, which pushes pixel colors onto the mesh; here the mesh is
colored first (by mesh_coloring.py, independently of the image) and its colors are
pulled back onto the photo.

For every masked pixel, pixel_to_vertex_nn.py already stored its top-K nearest
vertices and their cosine similarities. This takes those vertices' colors from a
mesh_coloring.py .pth and averages them weighted by similarity:

    pixel_color = sum_k(similarity_k * vertex_color_k) / sum_k(similarity_k)

With --k 1 that degenerates to "the color of the single best-matching vertex", which
keeps flat palette colors and sharp checkerboard edges in the image; larger --k blends
K palette colors into shades that are in no palette. Note the top-10 similarities of a
pixel typically differ by ~1%, so --k 10 is close to a plain average of 10 colors.

This is the figure SHIC shows (arXiv 2407.18907, Fig. 6): a textured mesh mapped over
the image through the predicted correspondences, where the regularity of the transferred
texture is the evidence -- a correspondence that respects the object's shape carries the
checkerboard over as recognizable, coherent patches; a bad one scatters it into speckle.

Which vertex colors to use is the whole choice here: `checker` (default) reads local
coherence, `position` reads global smoothness, `pca` shows what the features themselves
encode. All three come from mesh_coloring.py.

Run:
cd $DISC_ROOT && python analysis/color_image_from_knn.py \
  --mask_path ./demo/guitar/bsb/guitar_01_click_130_140_sam_mask_2.pth

Run (blend the 10 nearest vertices instead of taking the best one):
cd $DISC_ROOT && python analysis/color_image_from_knn.py \
  --mask_path ./demo/guitar/bsb/guitar_01_click_130_140_sam_mask_2.pth --k 10

Run (against the xyz coloring rather than the checkerboard):
cd $DISC_ROOT && python analysis/color_image_from_knn.py \
  --mask_path ./demo/guitar/bsb/guitar_01_click_130_140_sam_mask_2.pth \
  --vertex_colors_path ./demo/guitar/colored_mesh/guitar_mesh_position_color.pth

Caveat worth remembering when reading the output: the correspondence in the
*_pixel_to_vertex_nn.pth being used was computed against one specific pred_f.pth. The
default one in pixel_to_vertex_nn.py is the BSB authors' demo features, not our phase-1
retrain -- so a figure produced from it says nothing about our own encoder.
"""

import argparse
import os
import sys
import warnings

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.pixel_coloring import build_output_image


def check_mask_matches_knn(mask_path, knn, knn_path):
    """pixel_to_vertex_nn.py already stores exactly which (row, col) pixels it was
    computed from. Load the mask given now and check it marks the same pixels --
    catches a stale knn file computed against a different/older mask."""
    mask = torch.load(mask_path, map_location='cpu')
    mask_row, mask_col = torch.where(mask)
    same = (mask_row.shape == knn['pixel_row'].shape
            and torch.equal(mask_row, knn['pixel_row'])
            and torch.equal(mask_col, knn['pixel_col']))
    if not same:
        raise ValueError(f'{knn_path} was computed from a different mask than --mask_path={mask_path} '
                          f'({mask_row.shape[0]} masked pixels now vs {knn["pixel_row"].shape[0]} stored) -- '
                          f're-run pixel_to_vertex_nn.py against the current mask')


def load_knn(knn_path, k, mask_path):
    knn = torch.load(knn_path, map_location='cpu')
    top_k = knn['top_k']
    if not (1 <= k <= top_k):
        raise ValueError(f'k={k} must be in [1, {top_k}] (top_k stored in {knn_path})')
    check_mask_matches_knn(mask_path, knn, knn_path)
    return knn


def load_vertex_colors(vertex_colors_path, num_vertices):
    """The .pth written by mesh_coloring.py. Its `vertex_colors` are always indexed
    by the *original* mesh vertices, even for the checkerboard whose .ply carries
    split display geometry -- which is exactly what the correspondence indexes."""
    data = torch.load(vertex_colors_path, map_location='cpu')
    if 'vertex_colors' not in data:
        raise ValueError(f'{vertex_colors_path} has no "vertex_colors" '
                          '(expected a mesh_coloring.py output)')
    colors = data['vertex_colors']
    if colors.shape[0] != num_vertices:
        raise ValueError(f'{vertex_colors_path} has {colors.shape[0]} vertex colors, '
                          f'but the correspondence was computed on {num_vertices} vertices')
    print(f'vertex colors: {vertex_colors_path} (mode: {data.get("mode")}, '
          f'obj: {data.get("obj_path")})')
    return colors.float(), data


def back_project_colors(vertex_colors, topk_vertex_idx, topk_similarity, k):
    """[N_pixels, 3] float: each masked pixel's similarity-weighted mean of its k
    nearest vertices' colors."""
    idx = topk_vertex_idx[:, :k]                      # [N, k]
    weight = topk_similarity[:, :k]                   # [N, k]
    neighbor_colors = vertex_colors[idx]              # [N, k, 3]

    weight_sum = weight.sum(dim=1, keepdim=True)      # [N, 1]
    # Cosine similarity can be negative, so a row's weights can cancel out. Nothing
    # sensible to weight by then -- fall back to a plain mean for those pixels rather
    # than dividing by ~0 and painting noise.
    degenerate = weight_sum.abs().squeeze(1) < 1e-6
    if degenerate.any():
        warnings.warn(f'{int(degenerate.sum())} pixels have near-zero total similarity '
                      'over their k neighbors; using an unweighted mean for those')

    weighted = (neighbor_colors * weight.unsqueeze(-1)).sum(dim=1) / weight_sum.clamp(min=1e-6)
    uniform = neighbor_colors.mean(dim=1)
    return torch.where(degenerate.unsqueeze(1), uniform, weighted)


def save_side_by_side(mesh_render_path, img, output_path, background_color):
    """Mesh render on the left, back-projected photo on the right, scaled to a
    common height. The pair is the actual claim being made: these are the same
    colors, on the mesh and pulled through the correspondence onto the photo, so
    the two panels should be readable as the same object."""
    left = Image.open(mesh_render_path).convert('RGB')
    right = Image.fromarray(img)
    if right.mode == 'RGBA':  # flatten, a side-by-side sheet has no transparency
        flattened = Image.new('RGB', right.size, tuple(background_color))
        flattened.paste(right, mask=right.split()[3])
        right = flattened

    target_h = max(left.height, right.height)
    panels = []
    for panel in (left, right):
        scale = target_h / panel.height
        panels.append(panel.resize((max(1, int(panel.width * scale)), target_h)))

    combined = Image.new('RGB', (sum(p.width for p in panels), target_h),
                          tuple(background_color))
    x = 0
    for panel in panels:
        combined.paste(panel, (x, 0))
        x += panel.width
    combined.save(output_path)


def main(args):
    mask_basename = os.path.splitext(os.path.basename(args.mask_path))[0]
    knn_path = args.knn_path or os.path.join(
        args.knn_dir, f'{mask_basename}_pixel_to_vertex_nn.pth')

    knn = load_knn(knn_path, args.k, args.mask_path)
    num_vertices = knn['num_vertices']
    n_masked = knn['pixel_row'].shape[0]
    if n_masked == 0:
        raise ValueError(f'{knn_path} has zero masked pixels; nothing to color')

    vertex_colors, _ = load_vertex_colors(args.vertex_colors_path, num_vertices)

    source_tag = os.path.splitext(os.path.basename(args.vertex_colors_path))[0]
    output_path = args.output_path or os.path.join(
        args.save_dir, f'{mask_basename}_backproj_{source_tag}_k{args.k}.png')
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    pixel_colors = back_project_colors(vertex_colors, knn['topk_vertex_idx'],
                                       knn['topk_similarity'], args.k)

    used_weight = knn['topk_similarity'][:, :args.k]
    used_vertices = torch.unique(knn['topk_vertex_idx'][:, :args.k])
    print(f'correspondence: {knn_path}')
    print(f'masked pixels: {n_masked}, k: {args.k}')
    print(f'similarity (weight) used: mean={used_weight.mean().item():.4f} '
          f'min={used_weight.min().item():.4f} max={used_weight.max().item():.4f}')
    print(f'distinct vertices pulled from: {used_vertices.numel()}/{num_vertices} '
          f'({100.0 * used_vertices.numel() / num_vertices:.2f}%)')
    # With k=1 every pixel keeps one vertex's exact color, so this counts how many
    # palette entries survived; with k>1 it counts blends and will be large.
    distinct = torch.unique(pixel_colors.round().to(torch.int32), dim=0).shape[0]
    print(f'distinct pixel colors produced: {distinct}')

    background_image = None
    if args.source_image_path is not None:
        background_image = np.array(Image.open(args.source_image_path).convert('RGB'))
        if background_image.shape[:2] != knn['mask_shape']:
            raise ValueError(f'--source_image_path {args.source_image_path} is '
                             f'{background_image.shape[:2]}, mask is {knn["mask_shape"]}')

    img = build_output_image(knn['mask_shape'], knn['pixel_row'], knn['pixel_col'],
                             np.clip(np.round(pixel_colors.numpy()), 0, 255).astype(np.uint8),
                             args.background_color, args.transparent_background,
                             background_image=background_image, overlay_alpha=args.overlay_alpha)
    Image.fromarray(img).save(output_path)
    print(f'saved to {output_path}')

    if args.side_by_side:
        # Default: the render of exactly the coloring we pulled from, i.e.
        # <vertex_colors_path minus .pth>_rendered_views.png, which is what
        # render_colored_mesh.py writes next to it.
        mesh_render_path = args.mesh_render_path or (
            os.path.splitext(args.vertex_colors_path)[0] + '_rendered_views.png')
        if not os.path.exists(mesh_render_path):
            warnings.warn(f'{mesh_render_path} not found; skipping the side-by-side. '
                          'Render that .ply with render_colored_mesh.py first, or pass '
                          '--mesh_render_path.')
        else:
            side_by_side_path = args.side_by_side_path or (
                os.path.splitext(output_path)[0] + '_side_by_side.png')
            save_side_by_side(mesh_render_path, img, side_by_side_path, args.background_color)
            print(f'side-by-side (mesh render | back-projected photo) saved to {side_by_side_path}')
            # 2026-09-08, Tal: never keep both. The side-by-side's right panel is BIT-IDENTICAL to
            # the standalone PNG (verified 2026-09-07), so keeping both is pure duplication -- and
            # comparing a 1890x1080 side_by_side against an 810x1080 plain sheet has produced
            # mismatched-panel figures more than once. Seven scripts already did this `rm` by hand;
            # it belongs here instead. --keep_plain opts out; --no_side_by_side keeps the plain PNG
            # by construction (nothing else is written).
            if not args.keep_plain and os.path.abspath(side_by_side_path) != os.path.abspath(output_path):
                os.remove(output_path)
                print(f'removed the duplicate standalone {output_path} '
                      '(it is the right panel of the side-by-side; pass --keep_plain to keep it)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mask_path', type=str, required=True,
                         help='used only to derive the default --knn_path and the output filename '
                              '(the same mask pixel_to_vertex_nn.py was run on)')
    parser.add_argument('--knn_dir', type=str, required=True,
                         help='where to look for the pixel_to_vertex_nn.py output')
    parser.add_argument('--knn_path', type=str, default=None,
                         help='defaults to <knn_dir>/<mask_basename>_pixel_to_vertex_nn.pth')
    parser.add_argument('--vertex_colors_path', type=str,
                         default='./demo/guitar/colored_mesh/guitar_mesh_checker16_color.pth',
                         help='mesh_coloring.py .pth holding vertex_colors [V, 3] (checker, '
                              'position or pca -- this is what gets pulled back onto the photo)')
    parser.add_argument('--save_dir', type=str, default='./demo/guitar/back_projection/',
                         help='created if missing')
    parser.add_argument('--output_path', type=str, default=None,
                         help='defaults to <save_dir>/<mask_basename>_backproj_'
                              '<vertex_colors_basename>_k<k>.png')
    parser.add_argument('--k', type=int, default=1,
                         help='how many nearest vertices per pixel to average, weighted by cosine '
                              'similarity (must be <= the top_k stored in the correspondence). '
                              'k=1 is one vertex, i.e. flat palette colors and sharp edges; larger '
                              'k blends colors and softens everything.')
    parser.add_argument('--no_side_by_side', dest='side_by_side', action='store_false',
                         help='skip the mesh-render | back-projected-photo sheet')
    parser.add_argument('--keep_plain', action='store_true',
                         help='keep the standalone back-projection PNG alongside the side-by-side. '
                              'Off by default: the side-by-side already contains it, pixel for '
                              'pixel, as its right panel.')
    parser.add_argument('--mesh_render_path', type=str, default=None,
                         help='left panel of the side-by-side. Defaults to the render of the very '
                              'coloring being back-projected: <vertex_colors_path>_rendered_views.png '
                              '(what render_colored_mesh.py writes). Skipped with a warning if absent.')
    parser.add_argument('--side_by_side_path', type=str, default=None,
                         help='defaults to <output_path>_side_by_side.png')
    parser.add_argument('--source_image_path', type=str, default=None,
                         help='2026-09-03: the real photo to show OUTSIDE the mask instead of a '
                             'flat --background_color fill (e.g. the original --img_path). Must '
                             'match the mask\'s [H, W]. Ignored if --transparent_background is set '
                             '(alpha already makes the background invisible there).')
    parser.add_argument('--overlay_alpha', type=float, default=1.0,
                         help='2026-11-24: opacity of the colours inside the mask over --source_image_path '
                             '(1 = opaque, the old look; e.g. 0.6 lets the photo show through, like SHIC)')
    parser.add_argument('--background_color', nargs=3, type=int, default=[255, 255, 255],
                         help='RGB for pixels outside the mask (ignored if --source_image_path is set)')
    parser.add_argument('--transparent_background', type=int, default=None,
                         help='if set (0-255), output is RGBA with this alpha for background pixels')

    args = parser.parse_args()
    main(args)
