"""
pixel coloring: color every pixel of a SAM-segmented object, either by its DINO feature
(--mode pca) or by its 2D position in the mask (--mode position).

pca: reduced to RGB via PCA(3), following the pixel-coloring technique from
Amir et al., "Deep ViT Features as Dense Visual Descriptors"
(arXiv 2112.05814), code: github.com/ShirAmir/dino-vit-features/pca.py
(PCA fit directly on raw descriptors, then independent per-channel
min-max normalization to [0, 255]).

position: row -> R, col -> G, following DPC's create_colormap
(github.com/dvirginz/DPC/blob/main/visualization/mesh_visualization_utils.py),
which does per-axis min-max normalization of xyz -> RGB on a point cloud;
see position_colors() below for how this adapts to 2D.

Run:
cd $DISC_ROOT && python analysis/pixel_coloring.py \
  --mode pca --mask_path ./demo/guitar/bsb/guitar_01_click_130_140_sam_mask_2.pth
"""

import argparse
import os
import sys
import warnings

import numpy as np
import torch
from PIL import Image
from matplotlib.colors import hsv_to_rgb
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.utils import get_img_name, get_features_in_mask


def load_features(features_path):
    features = torch.load(features_path, map_location='cpu')
    if features.dtype != torch.float32:
        raise ValueError(f'expected float32 features, got {features.dtype}')
    if features.dim() != 3:
        raise ValueError(f'expected features of shape [H, W, F], got {tuple(features.shape)}')
    return features


def load_mask(mask_path):
    mask = torch.load(mask_path, map_location='cpu')
    if mask.dtype != torch.bool:
        raise ValueError(f'expected a bool mask, got {mask.dtype}')
    if mask.dim() != 2:
        raise ValueError(f'expected mask of shape [H, W], got {tuple(mask.shape)}')
    return mask


def _minmax_normalize(col, channel_label):
    col_min, col_max = col.min(), col.max()
    col_range = col_max - col_min
    if col_range < 1e-12:
        warnings.warn(f'{channel_label} channel has ~zero variance; setting it to 0')
        return np.zeros_like(col)
    return (col - col_min) / col_range


def pca_colors(features_in_mask, n_components, random_state):
    pca = PCA(n_components=n_components, random_state=random_state)
    reduced = pca.fit_transform(features_in_mask.detach().numpy())
    print('explained_variance_ratio_:', pca.explained_variance_ratio_)

    colors = np.zeros_like(reduced, dtype=np.float32)
    for c in range(n_components):
        colors[:, c] = _minmax_normalize(reduced[:, c], f'PCA component {c}')

    return (colors * 255).astype(np.uint8)


def pca_colors_shared(features_a, features_b, n_components, random_state):
    """Fit one PCA on the concatenation of features_a and features_b, then
    project each back separately. Unlike calling pca_colors() twice, the two
    outputs share a color space: equal colors in colors_a and colors_b then
    mean similar features, not just similar-within-their-own-set. Each PCA
    channel is min-max normalized jointly across both splits (not
    independently per split), so the shared scale actually holds.

    Returns (colors_a, colors_b), same uint8 [N, n_components] convention as
    pca_colors().
    """
    n_a = features_a.shape[0]
    pca = PCA(n_components=n_components, random_state=random_state)
    combined = torch.cat([features_a, features_b], dim=0).detach().numpy()
    reduced = pca.fit_transform(combined)
    print('explained_variance_ratio_ (shared basis):', pca.explained_variance_ratio_)

    colors = np.zeros_like(reduced, dtype=np.float32)
    for c in range(n_components):
        colors[:, c] = _minmax_normalize(reduced[:, c], f'PCA component {c}')
    colors = (colors * 255).astype(np.uint8)

    return colors[:n_a], colors[n_a:]


POSITION_B_CHANNEL = 128


def position_colors(mask_idx_row, mask_idx_col):
    """
    row -> R, col -> G, B fixed at POSITION_B_CHANNEL (no 3rd coordinate to
    encode). Per-axis min-max normalization is over this mask's own
    bounding box, mirroring DPC's create_colormap normalizing xyz over its
    own point cloud (see module docstring). B=0 was tried first but left
    much of the mask (anywhere row and col are both low) near-black;
    fixing B at a mid value instead raises the floor without changing what
    row/col actually encode (R, G are unaffected).

    Low contrast by construction: only two channels vary, and both vary
    linearly, so neighbouring pixels differ by very little. Use
    --position_palette wheel (position_colors_wheel below) when the point is
    to *see* small position differences.
    """
    row = mask_idx_row.numpy().astype(np.float32)
    col = mask_idx_col.numpy().astype(np.float32)
    colors = np.zeros((row.shape[0], 3), dtype=np.float32)
    colors[:, 0] = _minmax_normalize(row, 'row')
    colors[:, 1] = _minmax_normalize(col, 'col')
    colors = (colors * 255).astype(np.uint8)
    colors[:, 2] = POSITION_B_CHANNEL
    return colors


def position_colors_wheel(mask_idx_row, mask_idx_col, cycles=1.0,
                          saturation_floor=0.35, gamma=1.0):
    """Color-wheel encoding of 2D position -- much higher contrast than `rg`.

    Baker et al. 2007, the "Middlebury" optical-flow visualization: hue = angle
    around the mask's bounding-box centre, saturation = distance from it. This
    is the standard CV convention for showing a 2D position/displacement field,
    and it beats the `rg` scheme here for one reason: it uses the *hue circle*,
    where a small change in angle produces a large, easily-seen change in color
    (red -> orange -> yellow -> green -> ...), instead of two linear ramps
    confined to a corner of RGB space.

    `saturation_floor` keeps the centre of the object from washing out to white
    (plain Middlebury has saturation -> 0 there, which hides exactly the region
    with the most pixels on this mesh).

    `gamma` < 1 pushes saturation up faster with distance, spreading the
    mid-radius pixels apart; `gamma` > 1 does the opposite.

    `cycles` > 1 wraps the hue circle around more than once, so the color
    changes that many times faster with angle. It makes *local* differences
    dramatic, at the cost of global uniqueness -- two pixels at different angles
    can then share a color, so a smooth-looking mesh no longer proves the
    correspondence is globally right. Use it to inspect local structure, not to
    judge the whole map.
    """
    row = mask_idx_row.numpy().astype(np.float32)
    col = mask_idx_col.numpy().astype(np.float32)

    # Centre and scale on the mask's own bounding box, matching what
    # position_colors does, so the two palettes describe the same geometry.
    centered_row = 2.0 * _minmax_normalize(row, 'row') - 1.0
    centered_col = 2.0 * _minmax_normalize(col, 'col') - 1.0

    angle = np.arctan2(centered_row, centered_col)          # [-pi, pi]
    hue = np.mod(angle / (2.0 * np.pi) * cycles, 1.0)

    radius = np.sqrt(centered_row ** 2 + centered_col ** 2) / np.sqrt(2.0)
    radius = np.clip(radius, 0.0, 1.0) ** gamma
    saturation = saturation_floor + (1.0 - saturation_floor) * radius

    hsv = np.stack([hue, saturation, np.ones_like(hue)], axis=1)
    return (hsv_to_rgb(hsv) * 255).astype(np.uint8)


GOLDEN_RATIO_CONJUGATE = 0.6180339887


def position_colors_grid(mask_idx_row, mask_idx_col, grid=8):
    """Quantize position into a grid of cells, one distinct color per cell.

    Any *continuous* map from position to color is smooth by construction, so
    neighbouring pixels always look nearly identical no matter which colormap
    is used. Discretizing is the only thing that makes differences crisp.

    It is also the more useful diagnostic for correspondence: painted onto the
    mesh, a spatially coherent map shows large contiguous single-colour patches,
    and a scrambled one shows speckle. With a gradient, "slightly wrong" and
    "slightly different shade" look the same.

    Cell colours come from the golden-angle hue sequence
    (hue = cell_id * 0.618 mod 1), which is what makes *adjacent* cells differ
    strongly: consecutive ids land far apart on the hue circle instead of
    shading into each other the way a colormap indexed by cell number would.
    Lightness alternates on a checkerboard so that cells one row/column apart
    -- which the hue sequence can occasionally place close together -- still
    separate.
    """
    row = mask_idx_row.numpy().astype(np.float32)
    col = mask_idx_col.numpy().astype(np.float32)

    # Cell index within the mask's bounding box; the clip catches the single
    # pixel at the max edge, which would otherwise land in cell `grid`.
    row_cell = np.clip((_minmax_normalize(row, 'row') * grid).astype(np.int32), 0, grid - 1)
    col_cell = np.clip((_minmax_normalize(col, 'col') * grid).astype(np.int32), 0, grid - 1)

    cell_id = row_cell * grid + col_cell
    hue = np.mod(cell_id * GOLDEN_RATIO_CONJUGATE, 1.0)
    checker = (row_cell + col_cell) % 2
    saturation = np.where(checker == 0, 0.95, 0.65)
    value = np.where(checker == 0, 0.95, 0.75)

    hsv = np.stack([hue, saturation, value], axis=1)
    return (hsv_to_rgb(hsv) * 255).astype(np.uint8)


def build_output_image(shape_hw, mask_idx_row, mask_idx_col, pixel_colors,
                        background_color, transparent_background, background_image=None,
                       overlay_alpha=1.0):
    """background_image (2026-09-03, Tal): [H, W, 3] uint8, the real photo -- when given, it
    replaces the flat `background_color` fill everywhere OUTSIDE the mask, so the back-projected
    colors sit on the actual scene instead of blank white. `background_color` still applies
    outside the mask when this is None (unchanged default), and still supplies the RGB channels
    under a transparent background (alpha is what makes it invisible there, so the source photo
    would be redundant -- background_image is ignored when transparent_background is set)."""
    h, w = shape_hw
    if transparent_background is not None:
        img = np.zeros((h, w, 4), dtype=np.uint8)
        img[:, :, :3] = background_color
        img[:, :, 3] = transparent_background
        img[mask_idx_row, mask_idx_col, :3] = pixel_colors
        img[mask_idx_row, mask_idx_col, 3] = 255
    else:
        img = np.zeros((h, w, 3), dtype=np.uint8)
        if background_image is not None:
            if background_image.shape[:2] != (h, w):
                raise ValueError(f'background_image {background_image.shape[:2]} != mask shape {(h, w)}')
            img[:, :] = background_image
        else:
            img[:, :] = background_color
        if overlay_alpha < 1.0 and background_image is not None:
            # 2026-11-24 (Tal, Itai's task 3): see-through colours like SHIC's figures --
            # inside the mask, colour = a * colour + (1 - a) * photo. a = 1 keeps the old opaque look.
            photo = background_image[mask_idx_row, mask_idx_col].astype(np.float32)
            pixel_colors = np.clip(np.round(overlay_alpha * np.asarray(pixel_colors, np.float32)
                                            + (1.0 - overlay_alpha) * photo), 0, 255).astype(np.uint8)
        img[mask_idx_row, mask_idx_col] = pixel_colors

    return img


def main(args):
    mask = load_mask(args.mask_path)

    mask_basename = os.path.splitext(os.path.basename(args.mask_path))[0]
    mode_tag = args.mode
    if args.mode == 'position' and args.position_palette != 'rg':
        mode_tag = f'position_{args.position_palette}'
    output_path = args.output_path or os.path.join(args.save_dir, f'{mask_basename}_{mode_tag}_color.png')

    if args.mode == 'pca':
        img_name = get_img_name(args.img_path)
        features_path = args.features_path or os.path.join(args.save_dir, f'{img_name}_pix_dino_features.pth')
        features = load_features(features_path)
        if features.shape[:2] != mask.shape:
            raise ValueError(f'features spatial shape {tuple(features.shape[:2])} '
                              f'!= mask shape {tuple(mask.shape)}')
        features_in_mask, mask_idx_row, mask_idx_col = get_features_in_mask(features, mask)
        n_masked = features_in_mask.shape[0]
    else:
        mask_idx_row, mask_idx_col = torch.where(mask)
        n_masked = mask_idx_row.shape[0]

    transparent_background = None
    if args.transparent_background is not None:
        transparent_background = args.transparent_background

    if n_masked == 0:
        warnings.warn('mask has zero True pixels; writing a background-only image')
        img = build_output_image(mask.shape, mask_idx_row, mask_idx_col,
                                  np.zeros((0, 3), dtype=np.uint8),
                                  args.background_color, transparent_background)
        Image.fromarray(img).save(output_path)
        print(f'saved to {output_path}')
        return

    if args.mode == 'pca':
        if n_masked < args.n_components:
            raise ValueError(f'mask has only {n_masked} True pixels, '
                              f'fewer than n_components={args.n_components}')
        pixel_colors = pca_colors(features_in_mask, args.n_components, args.random_state)
    elif args.position_palette == 'rg':
        pixel_colors = position_colors(mask_idx_row, mask_idx_col)
    elif args.position_palette == 'wheel':
        pixel_colors = position_colors_wheel(mask_idx_row, mask_idx_col,
                                             cycles=args.position_cycles,
                                             saturation_floor=args.position_saturation_floor,
                                             gamma=args.position_gamma)
    else:
        pixel_colors = position_colors_grid(mask_idx_row, mask_idx_col,
                                            grid=args.position_grid)

    img = build_output_image(mask.shape, mask_idx_row, mask_idx_col, pixel_colors,
                              args.background_color, transparent_background)
    Image.fromarray(img).save(output_path)
    print(f'saved to {output_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, choices=['pca', 'position'], default='pca',
                         help='pca: color by DINO feature via PCA(3). '
                              'position: color by (row, col) in the mask.')
    parser.add_argument('--position_grid', type=int, default=8,
                         help='grid palette only. Cells per axis across the mask bounding box. '
                              'Larger = finer position resolution but smaller patches on the mesh.')
    parser.add_argument('--position_palette', type=str, choices=['rg', 'wheel', 'grid'], default='rg',
                         help="--mode position only. 'rg' (default, unchanged): row->R, col->G, "
                              "B fixed -- two linear ramps, low contrast. 'wheel': hue = angle "
                              'around the mask centre, saturation = distance (Baker et al. 2007 '
                              'optical-flow convention). Far more visible differences between '
                              "nearby pixels. Writes to <mask_basename>_position_wheel_color.png "
                              'so it never clobbers the rg output.')
    parser.add_argument('--position_cycles', type=float, default=1.0,
                         help='wheel palette only. How many times the hue circle wraps around the '
                              'object. >1 makes local color changes much sharper but destroys '
                              'global uniqueness (two different angles can share a color), so a '
                              'smooth mesh then no longer proves the correspondence is globally '
                              'right. Use for local inspection only.')
    parser.add_argument('--position_saturation_floor', type=float, default=0.35,
                         help='wheel palette only. Minimum saturation at the object centre. Plain '
                              'Middlebury uses 0, which washes the centre out to white -- exactly '
                              'where most of this mask lives.')
    parser.add_argument('--position_gamma', type=float, default=1.0,
                         help='wheel palette only. <1 raises saturation faster with distance from '
                              'the centre, spreading mid-radius pixels apart; >1 does the opposite.')
    parser.add_argument('--img_path', type=str, default='./images/guitar_01.png',
                         help='used only to derive the default features filename (--mode pca)')
    parser.add_argument('--save_dir', type=str, required=True)
    parser.add_argument('--features_path', type=str, default=None,
                         help='defaults to <save_dir>/<img_name>_pix_dino_features.pth (--mode pca)')
    parser.add_argument('--mask_path', type=str, required=True)
    parser.add_argument('--output_path', type=str, default=None,
                         help='defaults to <save_dir>/<mask_basename>_<mode>_color.png')
    parser.add_argument('--n_components', type=int, default=3, help='--mode pca only')
    parser.add_argument('--random_state', type=int, default=0, help='--mode pca only')
    parser.add_argument('--background_color', nargs=3, type=int, default=[255, 255, 255])
    parser.add_argument('--transparent_background', type=int, default=None,
                         help='if set (0-255), output is RGBA with this alpha for background pixels')

    args = parser.parse_args()
    main(args)
