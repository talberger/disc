"""Phase-2 encoder training: unified relational (distance-proportional) loss.

`train_mapping_loss.py` trains on two separately-weighted signals -- an
attractive mapping_loss and a repulsive hinge repulsion_loss, combined as
`lambda_map * map_loss + lambda_repel * repel_loss` -- which needed a
hand-derived `repel_margin` to reconcile pixel-space and mesh-space distance
scales. This is a separate experiment, starting from the same phase-1
checkpoint, that replaces the split with one continuous loss instead: for a
sample of center pixels and randomly-drawn in-segment/out-of-segment
neighbours (resampled every step), penalize pixel-space distance and
mesh-space distance for not being proportional -- see
modules/relational_loss.py for the full derivation and the Relational
Knowledge Distillation (Park et al., CVPR 2019) formalization it's based on.

train_mapping_loss.py and modules/mapping_loss.py are not modified by this
script -- those runs (encoder_dino_mapping_adjacent, encoder_dino_mapping_repel,
encoder_dino_mapping_repel_wide300) stay exactly reproducible. This script
imports several of train_mapping_loss.py's helpers directly (safe: that file
guards its argument-parsing/training invocation behind `if __name__ ==
'__main__':`) rather than duplicating them.

FIRST RUN (300 steps, 2026-08-10) COLLAPSED -- vertex coverage fell to 0.27%,
worse than mapping_loss's own original collapse. Root cause: normalizing
d_3D by a live, every-step mean is invariant to every pairwise 3D distance
shrinking together in proportion, and nothing stopped the model drifting
there over 300 steps of resampled-every-step neighbours. Two independent
fixes were designed to isolate which change actually matters (2026-08-11,
A/B, see `--live_mu_3d`/`--fixed_neighbors` below and modules/relational_loss.py's
module docstring for the full argument):

  Version 1 (default, both flags off): FIXED mu_3D_reference, measured once
    from the phase-1 encoder (measure_mu_3D_reference below); neighbours
    still resampled every step. The 2026-08-10 end-of-day fix.
  Version 2 (--live_mu_3d --fixed_neighbors): mu_3D back to LIVE (the
    original behavior); neighbours sampled ONCE and reused every step
    instead. Tal's 2026-08-11 hypothesis.

Run (from /workspace/bsb, so `modules.*` and `phase2.*` both resolve):
cd $DISC_ROOT && python -m phase2.train_relational_loss \\
    --object_mask_path <coarse mask> --pix_dino_features_path <pixel features> \\
    [--live_mu_3d --fixed_neighbors]   # add for Version 2

See /workspace/PROJECT_NOTES.md for the full design discussion.
"""
import argparse
import numpy as np
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F

from modules.cycle_consistency_loss import cycle_consistency_loss
from modules.cycle_consistency_loss_soft import cycle_consistency_loss_soft
from modules.cycle_consistency_loss_v2 import cycle_consistency_loss_v2, cycle_consistency_loss_v2_allpix
from modules.vertex_balance_loss import vertex_balance_loss
from modules.anchor_loss import anchor_loss
from modules.dist_loss import dist_loss
from modules.lora import apply_lora_w, lora_state, merged_state_dict
from modules.mapping_loss import (feature_drift, sample_center_pixels,
                                  sample_grid_center_pixels, soft_map_to_vertices)
from modules.feature_rkd_loss import (rkd_feat_angle3_loss, rkd_feat_dist_loss,
                                      rkd_feat_angle2_loss, hard_feature,
                                      measure_feature_mu_references, soft_feature,
                                      xseg_feat_loss, XSEG_FEAT_MODES)
from modules.relational_loss import (build_segment_index, relational_loss, rkd_spatial_dist_loss,
                                     sample_in_segment_neighbors, sample_out_segment_neighbors,
                                     rkd_spatial_angle3_loss)
from modules.utils import device, load_state_dict, loadmesh
from phase2.train_mapping_loss import (assert_resume_is_sane, get_fourier_basis, hash_input,
                                       load_phase1_encoder, set_fourier_basis)


def index_pixel_features(all_features, coords):
    """Per-step equivalent of train_mapping_loss.py's load_pixel_features,
    minus the disk read.

    That function re-reads the 3.6 GB [H, W, 1024] file from disk every call,
    which is fine there -- it's called once, since that script's neighbours
    are fixed for the whole run. Ours are resampled every step, so all_coords
    changes every step; re-reading the file from disk each time would mean
    a full 3.6 GB load + index + free per step, and was in fact the dominant
    cost the first time this script ran (~5.5s/step just in this call,
    measured). Fixed by reading the file once into `all_features` before the
    loop and only indexing it here -- same normalization, same detach, same
    reasoning (see load_pixel_features's docstring), just no repeated I/O.
    """
    features = all_features[coords[:, 0], coords[:, 1]].detach().to(device)
    return F.normalize(features.float(), dim=-1)


def aniso_mu_scale(mu_aniso, coords, neighbor_coords, center_groups):
    """DIRECTIONAL per-segment mu (--mu_scope segment_aniso, Tal 2026-09-21).

    Each segment g holds 3 numbers (a, b, c) -> L_g = [[e^a, 0], [c, e^b]], M_g = L_g L_g^T (always
    SPD: an ellipse). A pair's scale is s = sqrt(u^T M u) = |L^T u|, u = the unit IMAGE offset
    centre -> neighbour in (row, col). So s still divides the 3D side exactly like the isotropic mu;
    only WHICH value it takes depends on the pair's direction in the image. The direction is taken
    from the image because it is fixed data (the 3D direction would depend on the prediction itself).
    u and -u give the same s. a = b = log s0, c = 0 is a circle: s = s0 in every direction.

    mu_aniso [G, 3], coords [n, 2] (CPU), neighbor_coords [n, k, 2] (CPU), center_groups [n].
    Returns s [n, k] on mu_aniso's device.
    """
    return aniso_scale_from_params(mu_aniso[center_groups.to(mu_aniso.device).long()], coords, neighbor_coords)


def hybrid_aniso_mu_scale(mu_aniso, coords, neighbor_coords, center_groups, neighbor_groups):
    """--mu_scope segment_aniso_xglobal (Tal, 2026-09-27): an IN-segment pair uses its segment's ellipse
    (the part's proportions, as segment_aniso); a CROSS-segment pair uses ONE shared global ellipse, the
    LAST row of mu_aniso (placement, as global_aniso -- out-of-segment pairs are what separate the two
    front legs). neighbor_groups [n, k] = each neighbour's fine segment. Returns s [n, k]."""
    s_seg = aniso_mu_scale(mu_aniso[:-1], coords, neighbor_coords, center_groups)
    p_glob = mu_aniso[-1:].expand(coords.shape[0], 3)
    s_glob = aniso_scale_from_params(p_glob, coords, neighbor_coords)
    same = center_groups.to(s_seg.device).long().unsqueeze(1) == neighbor_groups.to(s_seg.device).long()
    return torch.where(same, s_seg, s_glob)


def switch_aniso_mu_scale(mu_aniso, coords, neighbor_coords, center_groups, global_phase):
    """--mu_scope global_then_segment_aniso (Tal, 2026-09-27): a two-stage schedule inside ONE run.
    Stage A (step < --mu_switch_step, global_phase=True): every pair uses ONE global ellipse = the LAST row of
    mu_aniso, and neighbours are drawn in+out of segment -- the cross-segment pairs fix left/right placement.
    Stage B: every pair uses its CENTRE's segment ellipse (rows 0..S-1), neighbours in-segment only (--switch_nin/_nout)
    -- the per-segment proportions. At the switch the segment rows are initialised from the global row."""
    if global_phase:
        return aniso_scale_from_params(mu_aniso[-1:].expand(coords.shape[0], 3), coords, neighbor_coords)
    return aniso_mu_scale(mu_aniso[:-1], coords, neighbor_coords, center_groups)


def dual_aniso_mu_scale(mu_aniso, coords, neighbor_coords, center_groups, n_global):
    """--mu_scope dual_global_local_aniso (Tal, 2026-10-01): TWO rkd_spatial_dist terms in the SAME step, 1:1.
    The first n_global neighbour columns are the GLOBAL term's pairs (in + out of segment) and use ONE shared ellipse
    (the LAST row of mu_aniso, as stage A of global_then_segment_aniso); the remaining columns are the LOCAL term's
    pairs (in-segment only) and use their centre's segment ellipse (rows 0..S-1, as stage B). Both sets are averaged in
    one Huber mean, so with equal column counts the two terms weigh 1:1. Unlike the hybrid, an in-segment pair of the
    global set is still held by the global ellipse."""
    s_glob = aniso_scale_from_params(mu_aniso[-1:].expand(coords.shape[0], 3), coords, neighbor_coords[:, :n_global])
    s_loc = aniso_mu_scale(mu_aniso[:-1], coords, neighbor_coords[:, n_global:], center_groups)
    return torch.cat([s_glob, s_loc], dim=1)


def grid_center_params(mu_grid, coords, bbox, grid):
    """--mu_scope grid_aniso: the (a, b, c) field lives on a grid x grid lattice of NODES spanning the
    mask's bounding box; each centre gets the BILINEAR interpolation of its 4 surrounding nodes, so the
    ellipse varies smoothly across the image instead of jumping at segment borders.
    mu_grid [grid*grid, 3] (row-major nodes), coords [n, 2] (row, col), bbox (rmin, rmax, cmin, cmax)."""
    rmin, rmax, cmin, cmax = bbox
    c = coords.float().to(mu_grid.device)
    fr = ((c[:, 0] - rmin) / max(rmax - rmin, 1) * (grid - 1)).clamp(0, grid - 1)
    fc = ((c[:, 1] - cmin) / max(cmax - cmin, 1) * (grid - 1)).clamp(0, grid - 1)
    r0 = fr.floor().long().clamp(max=grid - 2); c0 = fc.floor().long().clamp(max=grid - 2)
    wr = (fr - r0.float()).unsqueeze(1); wc = (fc - c0.float()).unsqueeze(1)
    node = lambda r, cc: mu_grid[r * grid + cc]
    return ((1 - wr) * (1 - wc) * node(r0, c0) + (1 - wr) * wc * node(r0, c0 + 1)
            + wr * (1 - wc) * node(r0 + 1, c0) + wr * wc * node(r0 + 1, c0 + 1))


def aniso_scale_from_params(p, coords, neighbor_coords):
    """s [n, k] = |L^T u| from per-CENTRE params p [n, 3] -- the shared core of both aniso scopes."""
    dp = (neighbor_coords - coords.unsqueeze(1)).float().to(p.device)             # [n, k, 2]
    norm = dp.norm(dim=-1, keepdim=True)
    # a neighbour identical to its centre has no direction (and d_2D = 0): give it the row axis;
    # any unit vector keeps s finite and > 0, and such a pair's residual does not depend on s anyway
    u = torch.where(norm > 0, dp / norm.clamp_min(1e-12), torch.tensor([1.0, 0.0], device=dp.device))
    ea, eb, c = p[:, 0].exp().unsqueeze(1), p[:, 1].exp().unsqueeze(1), p[:, 2].unsqueeze(1)
    x = ea * u[..., 0] + c * u[..., 1]                                           # (L^T u)_0
    y = eb * u[..., 1]                                                           # (L^T u)_1
    return torch.sqrt(x * x + y * y)


def aniso_axes(mu_aniso):
    """Per segment: principal scales (sqrt of M's eigenvalues, major >= minor) and the major axis's
    image angle in degrees (0 = along rows / vertical, 90 = along columns / horizontal)."""
    with torch.no_grad():
        a, b, c = mu_aniso[:, 0].exp(), mu_aniso[:, 1].exp(), mu_aniso[:, 2]
        L = torch.zeros(mu_aniso.shape[0], 2, 2, device=mu_aniso.device)
        L[:, 0, 0], L[:, 1, 0], L[:, 1, 1] = a, c, b
        M = L @ L.transpose(1, 2)
        evals, evecs = torch.linalg.eigh(M)                                      # ascending
        minor, major = evals[:, 0].sqrt(), evals[:, 1].sqrt()
        ang = torch.rad2deg(torch.atan2(evecs[:, 1, 1], evecs[:, 0, 1])) % 180.0
    return major, minor, ang


def measure_mu_3D_reference(encoder, vertices, coords, segment_ids, seg_idx, all_pixel_features,
                            k_vertices_per_pixel, num_neighbors_in_segment,
                            num_neighbors_out_segment, num_samples=5):
    """The FIXED mu_3D normalizer relational_loss() needs -- measured once,
    here, from the untouched phase-1 encoder, before any relational-loss
    training happens.

    The first version of relational_loss() recomputed mu_3D from the live,
    currently-training encoder's own output every step. That collapsed the
    first time it ran (postmortem in PROJECT_NOTES.md, 2026-08-10): a loss
    that only ever compares distances to its OWN batch's mean cannot see or
    resist every pairwise 3D distance shrinking together in proportion, so
    that direction was a free ride for 300 steps of gradient noise to drift
    down, and it did. A reference measured once, from a model this script
    has not yet touched, has nothing to do with wherever training later
    drifts -- restoring the role `repel_margin` played before normalization
    replaced it, just measured empirically instead of hand-picked.

    Averaged over `num_samples` independent random neighbour draws (the same
    sample_in_segment_neighbors/sample_out_segment_neighbors the training
    loop itself calls) rather than trusting a single draw, since any one
    draw of 2048*16 pairs is itself a sample with some variance.

    Returns a plain float.
    """
    num_centers = coords.shape[0]
    num_neighbors = num_neighbors_in_segment + num_neighbors_out_segment
    with torch.no_grad():
        vertex_features = encoder(vertices)
        draws = []
        for _ in range(num_samples):
            neighbor_coords_in = sample_in_segment_neighbors(
                coords, segment_ids, seg_idx, k=num_neighbors_in_segment)
            neighbor_coords_out = sample_out_segment_neighbors(
                coords, segment_ids, seg_idx, k=num_neighbors_out_segment)
            neighbor_coords = torch.cat([neighbor_coords_in, neighbor_coords_out], dim=1)

            all_coords = torch.cat([coords, neighbor_coords.reshape(-1, 2)], dim=0)
            pixel_features = index_pixel_features(all_pixel_features, all_coords)
            soft_points = soft_map_to_vertices(
                pixel_features, vertex_features, vertices, k_vertices_per_pixel)

            center_points = soft_points[:num_centers]
            neighbor_points = soft_points[num_centers:].view(num_centers, num_neighbors, 3)
            d_3D = (center_points.unsqueeze(1) - neighbor_points).pow(2).sum(-1).sqrt()
            draws.append(d_3D.mean().item())

    return sum(draws) / len(draws)


def measure_feature_mu(encoder, vertices, coords, segment_ids, seg_idx, all_pixel_features,
                      k_vertices_per_pixel, num_neighbors_in_segment, num_neighbors_out_segment,
                      temperature=1.0, num_samples=5, student_mode='soft', mu_stat='mean'):
    """The two FIXED feature-space normalizers rkd_feat_dist_loss() needs -- measured once, here,
    from the untouched phase-1 encoder, before any phase-2 training happens.

    Exactly the same construction, and the same reasoning, as measure_mu_3D_reference above: a
    normalizer taken from the live batch every step cannot see all distances shrinking together in
    proportion, which is how the original relational loss collapsed (PROJECT_NOTES.md 2026-08-10).
    Averaged over `num_samples` independent neighbour draws for the same reason it is there.

    The image side is frozen, so its mu is a genuine constant of the data; the mesh side is
    measured from phase-1 and then held while the encoder moves away from it -- which is the point.

    Returns (mu_img, mu_msh) as plain floats.
    """
    num_centers = coords.shape[0]
    num_neighbors = num_neighbors_in_segment + num_neighbors_out_segment
    with torch.no_grad():
        vertex_features = encoder(vertices)
        img_draws, msh_draws = [], []
        for _ in range(num_samples):
            neighbor_coords_in = sample_in_segment_neighbors(
                coords, segment_ids, seg_idx, k=num_neighbors_in_segment)
            neighbor_coords_out = sample_out_segment_neighbors(
                coords, segment_ids, seg_idx, k=num_neighbors_out_segment)
            neighbor_coords = torch.cat([neighbor_coords_in, neighbor_coords_out], dim=1)

            all_coords = torch.cat([coords, neighbor_coords.reshape(-1, 2)], dim=0)
            pixel_features = index_pixel_features(all_pixel_features, all_coords)
            _, topk_idx, weights = soft_map_to_vertices(
                pixel_features, vertex_features, vertices, k_vertices_per_pixel,
                return_topk=True, temperature=temperature)

            msh_all = (hard_feature if student_mode == 'argmax' else soft_feature)(
                vertex_features, topk_idx, weights)
            mu_img, mu_msh = measure_feature_mu_references(
                pixel_features[:num_centers],
                pixel_features[num_centers:].view(num_centers, num_neighbors, -1),
                msh_all[:num_centers],
                msh_all[num_centers:].view(num_centers, num_neighbors, -1),
                stat=mu_stat)
            img_draws.append(mu_img)
            msh_draws.append(mu_msh)

    return sum(img_draws) / len(img_draws), sum(msh_draws) / len(msh_draws)


def compute_bbox_diagonals(coarse_mask, vertices):
    """The two FIXED normalizers `--bbox_norm` needs -- each a plain
    geometric property of one domain's own data, computed once, before
    training, with no dependence on which pixels get sampled as centers/
    neighbours or on the encoder's live output at all.

    Unlike `measure_mu_3D_reference` (a MEAN over a sample of pairs, which
    inherits whatever imbalance that sample has -- on this mesh, centers are
    drawn uniform-over-pixels, so a segment's share of the 2048 centers is
    proportional to its pixel count: body 66.5%, neck 16.7%, headstock only
    4.5%), a bounding-box diagonal has nothing to do with sampling at all --
    it is a fixed fact about the whole object's extent, identical no matter
    which pixels or vertices happen to get drawn on a given step.

    Args:
        coarse_mask ndarray [H, W] bool  the object mask center pixels are
                                          drawn from
        vertices    tensor [V, 3]        mesh vertices (already loaded/
                                          normalized by loadmesh)

    Returns (bbox_diag_2D, bbox_diag_3D), both plain positive floats.
    """
    rows, cols = coarse_mask.nonzero()
    if rows.size == 0:
        raise ValueError('coarse_mask has zero True pixels -- cannot compute a bbox diagonal')
    height = float(rows.max() - rows.min() + 1)
    width = float(cols.max() - cols.min() + 1)
    bbox_diag_2D = (height ** 2 + width ** 2) ** 0.5

    mins = vertices.min(dim=0).values
    maxs = vertices.max(dim=0).values
    bbox_diag_3D = (maxs - mins).norm().item()

    for name, value in (('2D', bbox_diag_2D), ('3D', bbox_diag_3D)):
        if value is None or not (value == value) or value <= 0 or value == float('inf'):
            raise ValueError('computed bbox_diag_%s=%r is not a valid positive finite float -- '
                             'refusing to silently fall back to LIVE normalization under '
                             '--bbox_norm' % (name, value))

    return bbox_diag_2D, bbox_diag_3D


def default_geo_table_2d_path(geo_table_3d_path, object_mask_path, seed):
    """Shared by --geodesic and --cyc_weight>0 (cycle-consistency needs the 2D table even when
    --geodesic itself is off -- see modules/cycle_consistency_loss.py). Anchors to
    geo_table_3d_path's own directory (not a hardcoded one) so a custom --geo_table_3d_path
    still finds its matching 2D table alongside it, same as before this was factored out."""
    return os.path.join(os.path.dirname(geo_table_3d_path),
                        f'{os.path.splitext(os.path.basename(object_mask_path))[0]}'
                        f'_geo_table_2d_seed{seed}.pth')


def load_geodesic_table_2d(geo_table_2d_path, object_mask_path, coords, num_center_pixels, seed,
                           pool_mode=False):
    """Loads the 2D table (analysis/build_geodesic_tables.py) and verifies it was actually built
    against THIS run's centers/mask -- a stale or mismatched table would silently misattribute
    distances to the wrong pixels, exactly the class of bug check_mask_matches_knn already
    guards against elsewhere in this project's analysis scripts. Factored out of
    load_geodesic_tables so --cyc_weight>0 can load just this table without also requiring the
    (unrelated, --geodesic-only) 3D vertex-to-vertex table.

    pool_mode=False (default): existing exact-match behavior, byte-identical to before
    --resample_centers existed -- `coords` must be this run's fixed, already-sampled
    --num_center_pixels centers, and the table's every row is used every step.

    pool_mode=True (--resample_centers): `coords` is instead the FULL candidate pool from
    sample_grid_center_pixels (typically far more than num_center_pixels) -- the table's
    `num_center_pixels`/`seed` fields don't apply (that table was built with --center_mode
    grid, not random), so those checks are skipped in favor of checking `center_mode`/
    `grid_stride` instead. Returns the WHOLE pool table; the caller draws a fresh random
    row-subset from it every training step.

    Returns (geo_table_2d, geo_diag_2d float, pixel_to_node [H, W],
    geodesic_safe_mask bool ndarray [H, W]) -- all still on CPU. geo_table_2d is
    [num_center_pixels, M] in the default mode, [len(coords), M] (the whole pool) in pool_mode.
    """
    table_2d = torch.load(geo_table_2d_path, map_location='cpu')

    if pool_mode:
        if table_2d.get('center_mode') != 'grid':
            raise ValueError(f'{geo_table_2d_path} was not built with --center_mode grid '
                             f'(analysis/build_geodesic_tables.py) -- --resample_centers needs '
                             f'a candidate-pool table, not an exact-match one')
    else:
        if table_2d['num_center_pixels'] != num_center_pixels:
            raise ValueError(f'{geo_table_2d_path} was built with num_center_pixels='
                             f'{table_2d["num_center_pixels"]}, this run wants {num_center_pixels} '
                             f'-- rebuild the table or fix --num_center_pixels')
        if table_2d['seed'] != seed:
            raise ValueError(f'{geo_table_2d_path} was built with seed={table_2d["seed"]}, this run '
                             f'wants seed={seed} -- the sampled centers would not match')
    if os.path.basename(table_2d['object_mask_path']) != os.path.basename(object_mask_path):
        raise ValueError(f'{geo_table_2d_path} was built from mask '
                         f'{table_2d["object_mask_path"]!r}, this run\'s --object_mask_path is '
                         f'{object_mask_path!r} -- refusing to trust a table built from a '
                         f'different mask')
    if not torch.equal(table_2d['coords'], coords):
        raise ValueError(f'{geo_table_2d_path}\'s stored centers do not match the centers this '
                         f'run just sampled -- sample_center_pixels/sample_grid_center_pixels '
                         f'must have changed, or something else is inconsistent; table rows '
                         f'would silently line up with the wrong pixels otherwise')

    return (table_2d['table'], table_2d['diagonal'], table_2d['pixel_to_node'],
           table_2d['geodesic_safe_mask'].numpy())


def check_geo_table_3d_matches_mesh(table_3d, geo_table_3d_path, obj_path, num_vertices):
    """Guard against running with a 3D geodesic table built for a DIFFERENT mesh.

    Added 2026-09-02, when meshes/guitar_isotropic.obj entered the project. The 2D table has
    validated itself against its own mask/centers since it was written (load_geodesic_table_2d);
    the 3D table never did, because for a year there was only one mesh.

    The vertex-count check alone is not enough. Two meshes can share a vertex count and be
    completely different, and -- the reason this matters here -- modules.utils.loadmesh normalizes
    by `mean(vertices)`, the vertex CENTROID, so two triangulations of the SAME surface do not even
    live in the same coordinate frame. A mismatched table would not crash; it would silently train
    against another mesh's distances. So the table's recorded obj_path is compared too.
    """
    if table_3d.shape[0] != num_vertices:
        raise ValueError(
            f'3D geodesic table {geo_table_3d_path} is {tuple(table_3d.shape)} but the mesh at '
            f'{obj_path} has {num_vertices} vertices -- the table was built for a different mesh. '
            f'Rebuild it with scripts/build_geo_table_3d_only.py --obj_path {obj_path}')


def load_geodesic_tables(geo_table_3d_path, geo_table_2d_path, object_mask_path, coords,
                         num_center_pixels, seed, pool_mode=False):
    """Loads both precomputed tables (analysis/build_geodesic_tables.py) -- see
    load_geodesic_table_2d's docstring for the 2D-side validation this relies on, and for what
    pool_mode changes.

    Returns (geo_table_3d [V, V], geo_diag_3d float, geo_table_2d, geo_diag_2d,
    pixel_to_node [H, W], geodesic_safe_mask bool ndarray [H, W]) -- all
    tensors still on CPU, moved to `device` by the caller alongside everything else.
    """
    table_3d = torch.load(geo_table_3d_path, map_location='cpu')
    geo_table_2d, geo_diag_2d, pixel_to_node, geodesic_safe_mask = load_geodesic_table_2d(
        geo_table_2d_path, object_mask_path, coords, num_center_pixels, seed, pool_mode=pool_mode)

    return (table_3d['table'], table_3d['diagonal'], geo_table_2d, geo_diag_2d,
           pixel_to_node, geodesic_safe_mask)


def precompute_center_pixel_geodesic_distances(coords, geo_table_2d, pixel_to_node):
    """[num_centers, num_centers] pairwise GEODESIC pixel distance among this run's fixed
    center pixels, sliced directly out of the already-built 2D geodesic table -- no new
    geodesic computation. Same center_nodes lookup analysis/build_geodesic_tables.py's own
    build_2d_table uses for its dijkstra source nodes. Computed once (still CPU here -- caller
    moves the small result to `device`, same pattern as geodesic_distance_2d_lookup's own
    "only the small [n,k] RESULT crosses to the encoder's device" convention).
    """
    center_nodes = pixel_to_node[coords[:, 0], coords[:, 1]]
    if (center_nodes < 0).any():
        raise ValueError('a center pixel has no entry in the geodesic-safe mask (pixel_to_node '
                         '== -1) -- sample_center_pixels must be drawing against the same mask '
                         'build_geodesic_tables.py used')
    return geo_table_2d[:, center_nodes]


def save_loss_plot(losses, drifts, checkpoint_every, path):
    fig, (ax_loss, ax_drift) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    ax_loss.plot(losses)
    ax_loss.set_ylabel('relational loss')
    ax_loss.set_title('phase-2 relational loss training')
    ax_loss.grid(alpha=0.3)

    if drifts:
        steps, values = zip(*drifts)
        ax_drift.plot(steps, values, marker='o')
        ax_drift.set_ylabel('mean cosine vs phase 1')
        ax_drift.axhline(1.0, color='gray', linestyle=':', linewidth=1)
    ax_drift.set_xlabel('step')
    ax_drift.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def train(args):
    # Phase-2 was entirely unseeded until 2026-08-29: every torch.rand in the neighbour samplers
    # drew from the global RNG, so the same recipe never reproduced itself. Seeded in TWO places
    # -- here for the one-time setup draws (mu references, center sampling), and again immediately
    # before the training loop so the training stream does NOT depend on how much RNG the setup
    # happened to consume. That second reseed is what makes e.g. --feat_mu_mode fixed vs live a
    # clean A/B: 'live' skips measure_feature_mu's 5 draws, which would otherwise shift every
    # subsequent neighbour draw and confound the comparison.
    if args.out_neighbors_segmented_only:
        import modules.relational_loss as _rl
        _rl.OUT_NEIGHBORS_SEGMENTED_ONLY = True
    torch.manual_seed(args.train_seed)
    mesh = loadmesh(dir=args.obj_path, name=args.name, load_rings=True)
    vertices = mesh.vertices
    print('device=%s  vertices=%s' % (device, tuple(vertices.shape)))

    encoder = load_phase1_encoder(args)
    phase1_features = assert_resume_is_sane(
        encoder, vertices, os.path.join(args.init_encoder_dir, 'pred_f.pth'))

    if args.anchor_balance_from:
        # --anchor_balance_from (2026-09-10): the soft anchor's gradient is EXACTLY zero at
        # phase-1 (p == q), so its weight cannot be calibrated there. Move the encoder to a
        # drifted phase-2 checkpoint AFTER the resume gate (which must still see phase-1), and
        # keep phase1_features as the anchor's teacher.
        ckpt = torch.load(args.anchor_balance_from, map_location=device)
        load_state_dict(encoder, ckpt['encoder_state_dict'])
        set_fourier_basis(encoder, ckpt.get('fourier_basis'))
        with torch.no_grad():
            print('  [anchor_balance] encoder moved to %s (step %s), drift vs phase-1 %.4f'
                  % (args.anchor_balance_from, ckpt.get('step'),
                     feature_drift(encoder(vertices), phase1_features)))

    # Everything here stays on CPU: these coordinates index the 3.6 GB pixel
    # feature file below, and torch rejects a CUDA index against a CPU source.
    coarse_mask = torch.load(args.object_mask_path, map_location='cpu').numpy()
    fine_segments = torch.load(args.fine_seg_path, map_location='cpu').numpy()
    if args.geodesic:
        # Restrict to the largest connected component BEFORE sampling centers, matching
        # analysis/build_geodesic_tables.py's own fix (2026-09-03, found on demo/shic's bear3
        # mask: 5 components, one center landed on a dropped speck and build_2d_table crashed
        # with "some sample centers are not on-object pixels"). MUST mirror that script's
        # filtering exactly, or the centers sampled here will not match the geo_table_2d file's
        # stored ones and load_geodesic_tables's own consistency check rejects the run. Gated on
        # --geodesic only: Euclidean training never touches the 2D table and a speck center is
        # harmless there (see build_2d_table's docstring) -- restricting unconditionally would
        # silently change which centers existing Euclidean (guitar) runs draw, for no benefit.
        from analysis.build_geodesic_tables import largest_connected_component, occlusion_domain
        if args.geodesic_domain_mask_path:
            # OCCLUDED OBJECT (Tal, 2026-10-07): the table was built through the amodal domain, so the visible
            # pixels of EVERY part are usable -- same call as the table builder made (see occlusion_domain).
            coarse_mask, _domain = occlusion_domain(
                coarse_mask, torch.load(args.geodesic_domain_mask_path, map_location='cpu').numpy())
        else:
            coarse_mask, _num_components = largest_connected_component(coarse_mask)

    if args.resample_centers:
        if args.cyc_weight > 0.0:
            raise ValueError('--resample_centers is not implemented together with --cyc_weight '
                             '> 0 -- precompute_center_pixel_geodesic_distances is computed once '
                             'against a fixed center set, which --resample_centers breaks')
        if args.fixed_neighbors:
            raise ValueError('--resample_centers with --fixed_neighbors makes no sense: '
                             'fixed_neighbor_coords would be sampled once against ONE center '
                             'set and then reused against every step\'s different centers')
        if not args.geodesic:
            raise ValueError('--resample_centers currently requires --geodesic: in Euclidean '
                             'mode nothing stops a much larger, un-tabulated candidate pool, '
                             'but it has not been wired up (measure_mu_3D_reference etc. still '
                             'assume one fixed center set) -- ask if this is wanted')
        # CANDIDATE POOL (typically tens of thousands of pixels, not args.num_center_pixels) --
        # a fresh random subset of this becomes the actual centers every step, drawn below in
        # the training loop. Must be produced by the exact same call
        # (sample_grid_center_pixels(coarse_mask, fine_segments, stride)) the --center_mode grid
        # table build used, or the table's rows won't line up with these coordinates.
        candidate_coords, _, candidate_segment_ids = sample_grid_center_pixels(
            coarse_mask, fine_segments, stride=args.center_grid_stride)
        num_candidates = candidate_coords.shape[0]
        if args.num_center_pixels > num_candidates:
            raise ValueError(f'--num_center_pixels={args.num_center_pixels} exceeds the '
                             f'{num_candidates}-pixel candidate pool at --center_grid_stride='
                             f'{args.center_grid_stride} -- use a smaller stride or fewer '
                             f'centers per step')
        print('--resample_centers: %d candidate centers (grid stride %d), %d resampled fresh '
              'every step (was: %d centers sampled once, fixed for the whole run)'
              % (num_candidates, args.center_grid_stride, args.num_center_pixels,
                 args.num_center_pixels))
        # Placeholder for any one-time setup below that still wants SOME initial centers (e.g.
        # seg_idx doesn't need this, but keeping the variable defined keeps the rest of this
        # function's shape close to the non-resample path). Real per-step values are drawn
        # fresh in the training loop.
        step_center_idx = torch.randperm(num_candidates)[:args.num_center_pixels]
        coords = candidate_coords[step_center_idx]
        segment_ids = candidate_segment_ids[step_center_idx]
    else:
        # Centers: sampled once, fixed for the whole run (same convention as
        # train_mapping_loss.py). Only the 16 neighbours per center are resampled
        # every step -- see modules/relational_loss.py for why.
        coords, _, segment_ids = sample_center_pixels(
            coarse_mask, fine_segments, args.num_center_pixels, seed=args.seed)
    num_centers = coords.shape[0]
    print('sampled %d center pixels across %d segments'
          % (num_centers, len(torch.unique(segment_ids))))

    if args.geodesic:
        geo_table_2d_path = args.geo_table_2d_path or default_geo_table_2d_path(
            args.geo_table_3d_path, args.object_mask_path, args.seed)
        geo_table_3d, geo_diag_3d, geo_table_2d, geo_diag_2d, pixel_to_node, geodesic_safe_mask = \
            load_geodesic_tables(args.geo_table_3d_path, geo_table_2d_path,
                                 args.object_mask_path,
                                 candidate_coords if args.resample_centers else coords,
                                 args.num_center_pixels, args.seed,
                                 pool_mode=args.resample_centers)
        check_geo_table_3d_matches_mesh(geo_table_3d, args.geo_table_3d_path, args.obj_path,
                                        mesh.vertices.shape[0])
        table_3d_obj = torch.load(args.geo_table_3d_path, map_location='cpu').get('obj_path')
        if table_3d_obj is not None and os.path.realpath(table_3d_obj) != os.path.realpath(args.obj_path):
            raise ValueError(
                f'3D geodesic table {args.geo_table_3d_path} was built for {table_3d_obj} but this '
                f'run uses --obj_path {args.obj_path}. Same vertex count is NOT enough: loadmesh '
                f'normalizes by the vertex centroid, so two triangulations of the same surface sit '
                f'in different coordinate frames. Point --geo_table_3d_path at this mesh\'s table.')
        geo_table_3d = geo_table_3d.to(device)
        print('  geodesic tables loaded: 3D %s (diagonal=%.5f), 2D %s (diagonal=%.5f)'
              % (tuple(geo_table_3d.shape), geo_diag_3d, tuple(geo_table_2d.shape), geo_diag_2d))
        if args.geo_diag_2d is not None:
            # The stored 2D diagonal is a max over the SAMPLED CENTERS only (the table is
            # [num_centers, num_mask_pixels]), so it can only underestimate the true all-pairs
            # diameter. The 3D side has no such issue -- its table is all V x V pairs. Measured
            # 2026-09-08 with analysis/measure_2d_geodesic_diameter.py: true 1175.75 px vs the
            # stored 1171.65, a 0.35% underestimate.
            print('  geo_diag_2d OVERRIDE: %.5f -> %.5f (%+.2f%%)'
                  % (geo_diag_2d, args.geo_diag_2d,
                     100 * (args.geo_diag_2d - geo_diag_2d) / geo_diag_2d))
            geo_diag_2d = args.geo_diag_2d
        if args.geo_diag_3d is not None:
            # VISIBLE-PART normalizer (Tal, 2026-09-16, bear proportions): the table's diagonal is the WHOLE
            # mesh's diameter, which assumes the photo spans the whole object. For a partial view, pass the
            # geodesic diameter of the visible part (analysis/estimate_visible_geo_diameter.py). Fixed, never
            # refitted -- so unlike a fitted mu it keeps real zoom pressure on the features.
            print('  geo_diag_3d OVERRIDE: %.5f -> %.5f (%+.2f%%)'
                  % (geo_diag_3d, args.geo_diag_3d,
                     100 * (args.geo_diag_3d - geo_diag_3d) / geo_diag_3d))
            geo_diag_3d = args.geo_diag_3d

        if args.drop_pixels_mask_path:
            # DROPPED PIXELS (Tal, 2026-11-24, horse 170401): the lifted table's "red" pixels (in the mask, no surface point on the
            # lift; their vertex is borrowed from the nearest pixel). The SAME sampled centers and table are kept -- the dropped
            # centers' rows are removed, and the dropped pixels leave geodesic_safe_mask, so neighbour sampling (seg_idx below)
            # and the cycle's return leg never draw them.
            if args.resample_centers:
                raise ValueError('--drop_pixels_mask_path is not implemented with --resample_centers')
            drop = torch.load(args.drop_pixels_mask_path, map_location='cpu').numpy().astype(bool)
            keep_c = torch.from_numpy(~drop[coords[:, 0].numpy(), coords[:, 1].numpy()])
            coords, segment_ids, geo_table_2d = coords[keep_c], segment_ids[keep_c], geo_table_2d[keep_c]
            num_centers = coords.shape[0]
            geodesic_safe_mask = geodesic_safe_mask & ~drop
            print('  --drop_pixels_mask_path: %d dropped pixels, %d of %d centers dropped, %d centers left'
                  % (int(drop.sum()), int((~keep_c).sum()), len(keep_c), num_centers))

        # seg_idx must never be able to hand out one of the disconnected speck pixels as a
        # neighbour -- caught by a real smoke-test failure, not anticipated: the specks turned
        # out to carry a genuine fine_segment id (16 here), not background, so
        # sample_in_segment_neighbors (which draws from build_segment_index's
        # segment_pixel_coords, built from `fine_segments == s` ALONE -- it does not consult its
        # own `coarse_mask` argument at all, only `mask_coords`/`mask_segids` do) could still
        # draw them even after restricting `coarse_mask` to geodesic_safe_mask, which only fixed
        # sample_out_segment_neighbors's path. Fixed at the source instead: zero out
        # fine_segments at every non-geodesic-safe pixel in a COPY used only for this seg_idx,
        # so no segment's pixel list can ever contain one, regardless of build_segment_index's
        # own (mask-blind) construction of that structure. build_segment_index itself is
        # untouched -- every existing Euclidean run keeps calling it exactly as before.
        fine_segments_geodesic_safe = fine_segments.copy()
        fine_segments_geodesic_safe[~geodesic_safe_mask] = 0
        n_dropped = int((fine_segments != fine_segments_geodesic_safe).sum())
        if n_dropped > 0:
            print(f'  {n_dropped} disconnected pixel(s) zeroed out of fine_segments for '
                  f'neighbour sampling (were labeled with a real segment id despite being '
                  f'geodesically unreachable from the main mask component)')
        seg_idx = build_segment_index(fine_segments_geodesic_safe, geodesic_safe_mask)
    else:
        seg_idx = build_segment_index(fine_segments, coarse_mask)

    # build_segment_index now TOLERATES a segment with zero pixels (see its own comment: the
    # --geodesic copy above can empty out a segment that lies entirely outside the mask's largest
    # connected component). Tolerating it is only correct while no CENTER carries such a segment
    # id -- if one did, sample_in_segment_neighbors would compute
    # `(rand * 0).long().clamp(max=-1)` = -1 and silently draw the segment's last padding slot
    # instead of raising. That case has never been observed (geodesic_safe_mask is a subset of the
    # LCC that centers are drawn from), so fail loudly rather than train on garbage neighbours.
    center_segids = torch.unique(segment_ids)
    if args.resample_centers:
        center_segids = torch.unique(torch.cat([center_segids, candidate_segment_ids]))
    empty_centers = [int(s) for s in center_segids
                     if int(seg_idx.segment_pixel_count[int(s)]) == 0]
    if empty_centers:
        raise ValueError(
            f'center pixels belong to fine segment(s) {empty_centers} which have ZERO pixels in '
            f'the segment index -- in-segment neighbour sampling would silently draw padding. '
            f'This means geodesic_safe_mask dropped an entire segment that still owns centers; '
            f'see build_segment_index in modules/relational_loss.py.')

    num_neighbors = args.num_neighbors_in_segment + args.num_neighbors_out_segment
    if args.mu_scope == 'dual_global_local_aniso':
        num_neighbors += args.dual_local_nin          # global set (in + out) followed by the local set (in only)

    # Cycle-consistency needs a 2D geodesic table too, but is otherwise independent of
    # --geodesic (which is about d_2D/d_3D in relational_loss itself) -- reuse the table already
    # loaded above if --geodesic is on, else load just the 2D table. See
    # modules/cycle_consistency_loss.py for the full design.
    if args.cyc_weight > 0.0:
        if args.geodesic:
            cyc_geo_table_2d, cyc_geo_diag_2d, cyc_pixel_to_node = (
                geo_table_2d, geo_diag_2d, pixel_to_node)
        else:
            cyc_geo_table_2d_path = args.geo_table_2d_path or default_geo_table_2d_path(
                args.geo_table_3d_path, args.object_mask_path, args.seed)
            cyc_geo_table_2d, cyc_geo_diag_2d, cyc_pixel_to_node, _ = load_geodesic_table_2d(
                cyc_geo_table_2d_path, args.object_mask_path, coords,
                args.num_center_pixels, args.seed)
        # Normalized ONCE here (center_geo_dist is fixed for the whole run, unlike
        # rkd_spatial_dist_loss's own norm_d_2D which is recomputed every step against
        # resampled neighbours) -- same divide-by-geodesic-diameter convention as
        # relational_loss.py's norm_d_2D, so cyc_loss lands in roughly the same [0, ~1] range as
        # relational_loss instead of raw geodesic pixels (~0-1169.7px on this mesh/mask).
        # Tal's explicit call, following SHIC's own stated principle ("values that make the
        # losses roughly of similar scale") rather than reusing SHIC's literal beta -- our two
        # losses don't share SHIC's raw scale, but normalizing puts them on comparable footing so
        # --rkd_spatial_dist_weight/--cyc_weight sweep values are directly comparable, unlike raw pixels.
        center_geo_dist = precompute_center_pixel_geodesic_distances(
            coords, cyc_geo_table_2d, cyc_pixel_to_node).to(device) / max(cyc_geo_diag_2d, 1e-8)
        print('  cycle-consistency loss: ON (--cyc_weight %g, %s variant), round trip '
              'restricted to the %d fixed center pixels for both legs, geodesic-weighted, '
              'normalized by 2D geodesic diameter %.2fpx'
              % (args.cyc_weight,
                 ('V2 (all vertices, T=%g both legs, return to %s)'
                  % (args.cyc_temperature, 'ALL mask pixels' if args.cyc_return_all_pixels else 'the centers'))
                 if args.cyc_v2
                 else ('SOFT/no-snap' if args.cyc_soft else 'hard-snap'),
                 num_centers, cyc_geo_diag_2d))
    else:
        center_geo_dist = None

    # 2026-08-11 A/B test: which 2026-08-10 collapse fix actually matters,
    # the FIXED mu_3D_reference or FIXED (not resampled) neighbours? Both
    # default to the already-verified-safe combination (fixed reference,
    # resampled neighbours -- Version 1 below); --fixed_neighbors/
    # --live_mu_3d switch each axis independently. See
    # modules/relational_loss.py's module docstring for the full argument.
    if args.fixed_neighbors:
        neighbor_coords_in = sample_in_segment_neighbors(
            coords, segment_ids, seg_idx, k=args.num_neighbors_in_segment)
        neighbor_coords_out = sample_out_segment_neighbors(
            coords, segment_ids, seg_idx, k=args.num_neighbors_out_segment,
            max_retries=args.out_segment_max_retries)
        fixed_neighbor_coords = torch.cat([neighbor_coords_in, neighbor_coords_out], dim=1)
        print('  %d in-segment + %d out-of-segment neighbours per center, sampled ONCE '
              '(--fixed_neighbors) and reused every step'
              % (args.num_neighbors_in_segment, args.num_neighbors_out_segment))
    else:
        print('  %d in-segment + %d out-of-segment neighbours per center, resampled every step'
              % (args.num_neighbors_in_segment, args.num_neighbors_out_segment))

    # Loaded once, kept resident for the whole run (~3.6 GB) and indexed
    # in-memory every step -- see index_pixel_features's docstring for why
    # this can't reuse load_pixel_features's per-call disk read here.
    all_pixel_features = torch.load(args.pix_dino_features_path, map_location='cpu')

    # --flip_features_path (Tal, 2026-11-17, bear 6462: the zero-shot picks the same template flank for an image and its left-right
    # flip, so it is wrong on one of them): features of the image flipped left-right, and the template's mirror map (x -> -x, nearest
    # vertex). The flip term asks pixel (r, W-1-c) of the flipped image to land on the MIRROR of where pixel (r, c) lands.
    flip_pixel_features = flip_mirror = None
    if args.flip_weight > 0:
        flip_pixel_features = torch.load(args.flip_features_path, map_location='cpu')
        assert flip_pixel_features.shape == all_pixel_features.shape, (flip_pixel_features.shape, all_pixel_features.shape)
        from scipy.spatial import cKDTree
        _vn = vertices.detach().cpu().numpy()
        _d, _m = cKDTree(_vn).query(_vn * np.array([-1.0, 1.0, 1.0]))
        flip_mirror = torch.as_tensor(_m, device=device).long()
        print('FLIP term: weight %g, template mirror map median snap %.5f (template x extent %.4f)'
              % (args.flip_weight, float(np.median(_d)), float(np.ptp(_vn[:, 0]))))

    # --cyc_return_all_pixels (2026-09-10): the cycle's return leg over ALL mask pixels (SHIC as
    # written). Pixel features are gathered in 2D-table COLUMN order, so column j of the table and row j
    # of cyc_all_pixel_features are the same pixel. Both live on the GPU (~2 GB + ~1.7 GB).
    cyc_all_pixel_features = cyc_center_to_all = None
    if args.cyc_weight > 0.0 and args.cyc_v2 and args.cyc_return_all_pixels:
        on_mask_rc = (cyc_pixel_to_node >= 0).nonzero()
        coords_by_node = torch.empty((on_mask_rc.shape[0], 2), dtype=torch.long)
        coords_by_node[cyc_pixel_to_node[on_mask_rc[:, 0], on_mask_rc[:, 1]]] = on_mask_rc
        if cyc_geo_table_2d.shape[1] != coords_by_node.shape[0]:
            raise ValueError('2D table has %d columns but %d mask pixels were gathered'
                             % (cyc_geo_table_2d.shape[1], coords_by_node.shape[0]))
        # --cyc_return_stride (2026-09-13): return leg lands only on mask pixels on a regular
        # s-pixel grid (row % s == 0 and col % s == 0). Same table, column subset -- distances stay
        # exact. Cuts the [V x M] return softmax ~s^2 x, the cost that made all-pixel runs 15 min.
        #
        # SLICE FIRST (2026-09-20): this used to build BOTH full-size tensors -- the [2048 x 336278]
        # float32 distance table (2.75GB) and the [336278 x 2304] gathered feature matrix (3.1GB) --
        # normalize them, ship both to the GPU, and only THEN keep the stride-5 columns, which at
        # LVIS scale are 13452 of 336278 = 4% of what was just built. Measured: 58s of the phase-2
        # setup, and ~5.6GB of transient host+device memory, to produce ~230MB of tensors. Selecting
        # `keep` up front and indexing before .float()/normalize/.to(device) is bit-identical --
        # every op here is elementwise or per-row, so it commutes with taking a column subset -- and
        # it is what makes phase-2 fit comfortably beside the rest of the per-instance pipeline.
        keep = (slice(None) if args.cyc_return_stride <= 1 else
                ((coords_by_node[:, 0] % args.cyc_return_stride == 0)
                 & (coords_by_node[:, 1] % args.cyc_return_stride == 0)).nonzero().squeeze(1))
        if args.drop_pixels_mask_path:      # the return leg never lands on a dropped pixel either
            keep = torch.arange(coords_by_node.shape[0])[keep]
            keep = keep[torch.from_numpy(~drop[coords_by_node[keep, 0].numpy(), coords_by_node[keep, 1].numpy()])]
        kept_coords = coords_by_node[keep]
        cyc_all_pixel_features = F.normalize(
            all_pixel_features[kept_coords[:, 0], kept_coords[:, 1]].float(), dim=-1).to(device)
        cyc_center_to_all = (cyc_geo_table_2d[:, keep].float()
                             / max(cyc_geo_diag_2d, 1e-8)).to(device)
        print('  cycle v2 return leg: %d mask pixels (%s), table [%d x %d] on GPU'
              % (cyc_all_pixel_features.shape[0],
                 'ALL, SHIC as written' if args.cyc_return_stride == 1 else
                 'grid stride %d' % args.cyc_return_stride,
                 cyc_center_to_all.shape[0], cyc_center_to_all.shape[1]))

    def _cyc_v2(center_pf, vf):
        if args.cyc_return_all_pixels:
            # chunk size scaled so memory per chunk stays what it was at the full 212k pixels
            return cycle_consistency_loss_v2_allpix(
                center_pf, vf, cyc_all_pixel_features, cyc_center_to_all, args.cyc_temperature,
                chunk_size=max(256, 256 * 212549 // cyc_all_pixel_features.shape[0]))
        return cycle_consistency_loss_v2(center_pf, vf, center_geo_dist, args.cyc_temperature)

    if sum([args.bbox_norm, args.live_mu_3d, args.geodesic]) > 1:
        raise ValueError('--bbox_norm, --live_mu_3d, and --geodesic are mutually exclusive '
                         'normalization/distance modes -- pick exactly one (or none, for the '
                         'FIXED-mean-from-phase-1 default).')

    if args.geodesic:
        # Geodesic diameters (max pairwise geodesic distance), not Euclidean bbox diagonals --
        # Tal's explicit call: since the distances themselves are now geodesic, the reference
        # they're compared against should be too, matching SHIC's own convention of normalizing
        # by the max geodesic distance on the mesh. See modules/relational_loss.py's geodesic-
        # variant docstring for the full design.
        mu_2D_reference, mu_3D_reference = geo_diag_2d, geo_diag_3d
        print('  normalization: GEODESIC (--geodesic) -- d_2D / %.2fpx (2D geodesic diameter), '
              'd_3D / %.5f (3D geodesic diameter), both fixed' % (mu_2D_reference, mu_3D_reference))
    elif args.bbox_norm:
        # FIXED bounding-box-diagonal normalizers for BOTH d_2D and d_3D --
        # see compute_bbox_diagonals's docstring for why this is immune to
        # the segment-sampling imbalance that a mean-of-pairs normalizer
        # (either mode below) inherits. mu_2D_reference is asserted non-None
        # here on purpose: if compute_bbox_diagonals ever returned something
        # that couldn't be trusted, we want a loud failure, not a silent
        # fall-through to relational_loss's None-means-LIVE default.
        mu_2D_reference, mu_3D_reference = compute_bbox_diagonals(coarse_mask, vertices)
        assert mu_2D_reference is not None and mu_3D_reference is not None
        print('  normalization: BBOX (--bbox_norm) -- d_2D / %.2fpx (coarse mask bbox '
              'diagonal), d_3D / %.5f (mesh vertex bbox diagonal), both fixed, neither a '
              'sampled-pair statistic' % (mu_2D_reference, mu_3D_reference))
    elif args.live_mu_3d:
        # LIVE mode: mu_3D recomputed from the live encoder every step, same
        # as the original (pre-2026-08-10-fix) relational_loss(). Known to
        # collapse when paired with resampled-every-step neighbours; this
        # session is testing it paired with --fixed_neighbors instead.
        mu_2D_reference = None
        mu_3D_reference = None
        print('  mu_3D: LIVE (--live_mu_3d) -- recomputed from the training encoder every step')
    else:
        # FIXED normalizer for relational_loss's d_3D, measured once from the
        # untouched phase-1 encoder -- see measure_mu_3D_reference's docstring
        # for why this must not be recomputed from the live encoder every step.
        mu_2D_reference = None
        mu_3D_reference = measure_mu_3D_reference(
            encoder, vertices, coords, segment_ids, seg_idx, all_pixel_features,
            args.k_vertices_per_pixel, args.num_neighbors_in_segment,
            args.num_neighbors_out_segment, num_samples=args.mu_3d_reference_samples)
        print('  mu_3D reference (fixed, phase-1 encoder, averaged over %d draws): %.5f'
              % (args.mu_3d_reference_samples, mu_3D_reference))

    # Feature-space RKD normalizers (added 2026-08-28). Measured from the same untouched phase-1
    # encoder as mu_3D above, for the same anti-collapse reason. Skipped entirely when neither
    # feature term is in use and nothing asked for their magnitudes.
    mu_img_reference = mu_msh_reference = None
    if (args.rkd_feat_dist_weight > 0.0 or args.rkd_feat_angle3_weight > 0.0
            or args.rkd_feat_angle2_weight > 0.0 or args.log_feature_terms
            or args.rkd_feat_angle2_balance):
        if args.feat_mu_mode == 'fixed':
            mu_img_reference, mu_msh_reference = measure_feature_mu(
                encoder, vertices, coords, segment_ids, seg_idx, all_pixel_features,
                args.k_vertices_per_pixel, args.num_neighbors_in_segment,
                args.num_neighbors_out_segment, temperature=args.temperature,
                num_samples=args.mu_3d_reference_samples,
                student_mode=args.feat_student_mode, mu_stat=args.feat_mu_stat)
            print('  feature-RKD mu references (fixed, phase-1 encoder, %d draws, stat=%s): '
                  'mu_img=%.5f  mu_msh=%.5f'
                  % (args.mu_3d_reference_samples, args.feat_mu_stat,
                     mu_img_reference, mu_msh_reference))
        else:
            print('  feature-RKD mu: LIVE per batch (the RKD paper\'s own choice)')
        print('  feature-RKD student: %s'
              % ('ARGMAX (k=1, no mixing -- gradient lands on one vertex per pixel)'
                 if args.feat_student_mode == 'argmax' else 'soft (weighted average over k)'))
        print('  feature-RKD soft-map weights: %s'
              % ('DETACHED (circularity test -- gradient can only move features)'
                 if args.feat_detach_weights else 'attached (default)'))
        # 2026-09-04: the pair-angle weight MUST be printed here too. It was missing when the flag
        # was added, so a run with only the pair-angle term on printed "beta=0, gamma=0" and read
        # as though no feature term were active at all -- exactly backwards.
        print('  feature-RKD weights: rkd_feat_dist=%g, rkd_feat_angle3=%g, '
              'rkd_feat_angle2=%g%s'
              % (args.rkd_feat_dist_weight, args.rkd_feat_angle3_weight, args.rkd_feat_angle2_weight,
                 '  [logging only, no feature term is in the optimized loss]'
                 if (args.rkd_feat_dist_weight == 0.0 and args.rkd_feat_angle3_weight == 0.0
                     and args.rkd_feat_angle2_weight == 0.0) else ''))
        print('  feature-RKD detach: features=%s, weights=%s  (gradFW = neither, '
              'gradF = weights detached, gradW = features detached)'
              % (args.feat_detach_features, args.feat_detach_weights))
        if args.rkd_spatial_dist_weight == 0.0:
            print('  *** rkd_spatial_dist_weight=0: the SPATIAL term is OFF -- nothing anchors the map '
                  'to geometry (2026-09-04: this diverged when tried) ***')

    xseg_on = args.xseg_feat_mode != 'off'
    frozen_vertex_unit = None
    if xseg_on:
        # 'table' student: the phase-1 vertex features, unit norm, frozen for the whole run (C = their cosines)
        frozen_vertex_unit = F.normalize(phase1_features.detach().float(), dim=-1)
        print('  XSEG: %d in-segment pairs per centre -> rkd_spatial_dist (segment ellipse); %d cross-segment pairs '
              '-> feature RKD, mode %s, weight %g%s'
              % (args.num_neighbors_in_segment, args.num_neighbors_out_segment, args.xseg_feat_mode,
                 args.xseg_feat_weight, '  [BALANCE diagnostic at step %d]' % args.xseg_feat_balance_step
                 if args.xseg_feat_balance else ''))

    print('  distance_weight: %s' % (args.distance_weight or 'none (every pair weighted equally)'))
    if args.anchor_weight > 0.0 or args.anchor_balance_from:
        print('  ZS anchor: weight=%g T=%g target=%s (CE over all %d vertices vs frozen phase-1, '
              'see modules/anchor_loss.py)'
              % (args.anchor_weight, args.anchor_temperature,
                 'HARD argmax (SHIC L_pseudo)' if args.anchor_hard else 'SOFT q_ZS',
                 vertices.shape[0]))
    # SHIC L_dist (2026-09-12). Needs the 3D geodesic table, which only the --geodesic branch
    # loads -- fail loudly rather than silently skipping the term.
    dist_target_idx = None
    if args.dist_weight > 0.0 or args.dist_balance:
        if not args.geodesic:
            raise ValueError('--dist_weight/--dist_balance need the 3D geodesic table, which is only '
                             'loaded under --geodesic. Add --geodesic (the current recipe uses it).')
        print('  SHIC L_dist: weight=%g T_dist=%g (E_p[geodesic distance to %s] / %.5f, '
              'over all %d vertices -- see modules/dist_loss.py)'
              % (args.dist_weight, args.dist_temperature,
                 'the ZS argmax' if args.dist_soft_target_temperature is None else
                 'y ~ SOFT q_ZS at T=%g' % args.dist_soft_target_temperature,
                 geo_diag_3d, vertices.shape[0]))
    # MU-LEARNED (2026-09-14, Tal) -- mu_3d_scale is the proportion/zoom coefficient between the two
    # normalized distance spaces. It used to be a hand-swept constant; it can now be FITTED.
    #   --mu_mode fixed    the constant in --mu_3d_scale (default, bit-identical to every old run)
    #   --mu_mode optimal  closed-form least-squares refit EVERY step (no parameter, no lr)
    #   --mu_mode learned  an nn.Parameter trained by Adam alongside the encoder
    #   --mu_scope global|segment   one scale for everything, or one per fine segment
    # A pair's group is its CENTRE's segment (the simple choice; an out-of-segment pair therefore
    # belongs to the centre's segment, not the neighbour's).
    mu_log_scale = None
    mu_aniso = None
    mu_groups = None
    mu_n_groups = None
    mu_seg_map = None
    if args.mu_mode != 'fixed':
        if not args.geodesic:
            raise SystemExit('--mu_mode %s is only implemented for the geodesic loss' % args.mu_mode)
        if args.mu_scope in ('segment_aniso', 'grid_aniso', 'global_aniso', 'segment_aniso_xglobal', 'global_then_segment_aniso', 'dual_global_local_aniso'):
            if args.mu_mode != 'learned':
                raise SystemExit('--mu_scope %s is implemented for --mu_mode learned only' % args.mu_scope)
            # global_aniso: ONE ellipse, so an out-of-segment pair has no ambiguity -- allowed (Tal, 2026-09-27)
            # --xseg_feat_mode: the out-of-segment pairs never reach rkd_spatial_dist, so they need no ellipse
            if (args.num_neighbors_out_segment > 0 and args.xseg_feat_mode == 'off'
                    and args.mu_scope not in ('global_aniso', 'segment_aniso_xglobal', 'global_then_segment_aniso', 'dual_global_local_aniso')):
                raise SystemExit('--mu_scope segment_aniso: out-of-segment pairs have no single segment '
                                 'ellipse (the isotropic path uses a geometric mean) -- not defined yet; '
                                 'use --num_neighbors_out_segment 0')
        if args.mu_scope in ('segment', 'segment_aniso'):
            seg_vals = torch.unique(segment_ids)
            mu_n_groups = int(max(seg_vals.max().item(), int(fine_segments.max())) ) + 1
            mu_groups = segment_ids.to(device).long()          # [n], broadcast over the k pairs
            # the fine-segment map, so each NEIGHBOUR pixel's segment is available per step
            # (fixes 1 and 2: fit from in-segment pairs, geometric mean across segments)
            mu_seg_map = torch.as_tensor(fine_segments, device=device).long()
        elif args.mu_scope == 'global_then_segment_aniso':
            # same layout as the hybrid: rows 0..S-1 per fine segment, the LAST row = the stage-A global ellipse
            if args.mu_switch_step is None or args.fixed_neighbors:
                raise SystemExit('--mu_scope global_then_segment_aniso needs --mu_switch_step (and no --fixed_neighbors)')
            if args.switch_nin + args.switch_nout != args.num_neighbors_in_segment + args.num_neighbors_out_segment:
                raise SystemExit('--switch_nin + --switch_nout must equal the stage-A neighbour count (tensor shapes)')
            seg_vals = torch.unique(segment_ids)
            mu_n_groups = int(max(seg_vals.max().item(), int(fine_segments.max()))) + 1 + 1
            mu_groups = segment_ids.to(device).long()
            mu_seg_map = torch.as_tensor(fine_segments, device=device).long()
        elif args.mu_scope == 'dual_global_local_aniso':
            # same layout as the two-stage: rows 0..S-1 per fine segment (LOCAL term), the LAST row = the GLOBAL term's ellipse
            if args.fixed_neighbors or args.dual_local_nin <= 0:
                raise SystemExit('--mu_scope dual_global_local_aniso needs --dual_local_nin > 0 (and no --fixed_neighbors)')
            seg_vals = torch.unique(segment_ids)
            mu_n_groups = int(max(seg_vals.max().item(), int(fine_segments.max()))) + 1 + 1
            mu_groups = segment_ids.to(device).long()
            mu_seg_map = torch.as_tensor(fine_segments, device=device).long()
        elif args.mu_scope == 'segment_aniso_xglobal':
            # one ellipse per fine segment (rows 0..S-1, indexed by segment id) + ONE global ellipse
            # (the last row) for cross-segment pairs -- see hybrid_aniso_mu_scale
            seg_vals = torch.unique(segment_ids)
            mu_n_groups = int(max(seg_vals.max().item(), int(fine_segments.max()))) + 1 + 1
            mu_groups = segment_ids.to(device).long()
            mu_seg_map = torch.as_tensor(fine_segments, device=device).long()
        elif args.mu_scope == 'global_aniso':
            # ONE ellipse for the whole object (Tal, 2026-09-21); neighbour sampling is untouched
            # (still in-segment) -- only mu stops being per segment
            mu_n_groups = 1
            mu_groups = torch.zeros_like(segment_ids).to(device).long()
        elif args.mu_scope == 'grid_aniso':
            mu_n_groups = args.mu_grid * args.mu_grid      # one (a, b, c) per lattice NODE
            mu_groups = None
            _r, _c = coarse_mask.nonzero()
            mu_grid_bbox = (float(_r.min()), float(_r.max()), float(_c.min()), float(_c.max()))
        else:
            mu_n_groups = 1
            mu_groups = None
        if args.mu_mode == 'learned' and args.mu_scope in ('segment_aniso', 'grid_aniso', 'global_aniso', 'segment_aniso_xglobal', 'global_then_segment_aniso', 'dual_global_local_aniso'):
            # [G, 3] = (a, b, c); a = b = log s0, c = 0 -> a circle of radius s0 (s0 = 1, or --mu_init_path)
            init = torch.ones(mu_n_groups)
            if args.mu_init_path is not None:
                init = torch.load(args.mu_init_path, map_location='cpu')['mu_scale'].float()
                if init.numel() != mu_n_groups:
                    raise SystemExit('--mu_init_path has %d scales, run has %d groups' % (init.numel(), mu_n_groups))
            mu_aniso = torch.zeros(mu_n_groups, 3)
            mu_aniso[:, 0] = mu_aniso[:, 1] = init.clamp_min(1e-6).log()
            if args.mu_aniso_fixed_path is not None and args.mu_scope == 'segment_aniso_xglobal':
                # HAND-MADE per-seg ellipses + a hand-made global (cross-seg) row, ALL frozen from step 0 (Tal, 2026-09-28)
                fixed = torch.load(args.mu_aniso_fixed_path, map_location='cpu')['mu_aniso'].float()
                if fixed.shape[0] != mu_n_groups:
                    raise SystemExit('--mu_aniso_fixed_path has %d rows, run has %d (segments + 1 global)' % (fixed.shape[0], mu_n_groups))
                mu_aniso = fixed.clone()
                print('  mu_aniso LOADED + FROZEN (all rows) from %s' % args.mu_aniso_fixed_path)
            if args.stageA_fixed:
                # two-stage, HAND-MADE from step 0 (Tal, 2026-09-29): stage A reads the manual GLOBAL row, stage B (hybrid)
                # the manual segment rows + the same global row; all rows frozen for the whole run
                if not (args.mu_scope == 'global_then_segment_aniso' and args.switch_hybrid and args.mu_aniso_fixed_path is not None):
                    raise SystemExit('--stageA_fixed needs global_then_segment_aniso + --switch_hybrid + --mu_aniso_fixed_path')
                fixed = torch.load(args.mu_aniso_fixed_path, map_location='cpu')['mu_aniso'].float()
                if fixed.shape[0] != mu_n_groups:
                    raise SystemExit('--mu_aniso_fixed_path has %d rows, run has %d (segments + 1 global)' % (fixed.shape[0], mu_n_groups))
                mu_aniso = fixed.clone()
                print('  stage A: mu_aniso LOADED + FROZEN (all rows) from %s, global row %s'
                      % (args.mu_aniso_fixed_path, [round(x, 3) for x in fixed[-1].tolist()]))
            if args.stageA_fixed_circle is not None:
                # stage A global = a FROZEN circle of this mu (Tal, 2026-09-29); stage B per-seg rows start from it and LEARN
                if args.mu_scope != 'global_then_segment_aniso':
                    raise SystemExit('--stageA_fixed_circle needs --mu_scope global_then_segment_aniso')
                mu_aniso[-1, 0] = mu_aniso[-1, 1] = float(torch.tensor(args.stageA_fixed_circle).log()); mu_aniso[-1, 2] = 0.0
                print('  stage A: global ellipse FROZEN to circle %g' % args.stageA_fixed_circle)
            mu_aniso = mu_aniso.to(device).requires_grad_(True)
            if (args.mu_aniso_fixed_path is not None and args.mu_scope == 'segment_aniso_xglobal') or args.stageA_fixed:
                mu_aniso.register_hook(lambda g: torch.zeros_like(g))
            if args.stageA_fixed_circle is not None:
                _gmask = torch.ones_like(mu_aniso); _gmask[-1] = 0          # the global row never updates (zero grad, zero Adam moments)
                mu_aniso.register_hook(lambda g: g * _gmask)
        elif args.mu_mode == 'learned':
            mu_log_scale = torch.zeros(mu_n_groups, device=device, requires_grad=True)
            if args.mu_init_path is not None:
                # per-group scales precomputed from a frozen reference mapping (analysis/perseg_mu_from_zs.py,
                # Tal 2026-09-16). With --mu_lr 0 they stay FIXED for the whole run.
                init = torch.load(args.mu_init_path, map_location='cpu')['mu_scale'].float()
                if init.numel() != mu_n_groups:
                    raise SystemExit('--mu_init_path has %d scales, run has %d groups' % (init.numel(), mu_n_groups))
                with torch.no_grad():
                    mu_log_scale.copy_(init.clamp_min(1e-6).log().to(device))
                print('  mu_3d_scale INIT from %s: %s (mu_lr %g)'
                      % (args.mu_init_path, [round(x, 3) for x in init.tolist()], args.mu_lr))
        print('  mu_3d_scale: %s, scope %s%s -- the zoom between norm_d_2D and norm_d_3D is %s'
              % (args.mu_mode, args.mu_scope,
                 '' if mu_n_groups == 1 else ' (%d segments)' % mu_n_groups,
                 'refit in closed form every step' if args.mu_mode == 'optimal'
                 else 'a DIRECTIONAL 2x2 SPD metric per segment (3 Adam-trained params, init = a circle)'
                 if mu_aniso is not None else 'an Adam-trained parameter (init 1.0)'))
    else:
        print('  mu_3d_scale: %g%s' % (args.mu_3d_scale, ' (no-op)' if args.mu_3d_scale == 1.0 else ''))
    if args.balance_weight > 0.0:
        print('  vertex-balance loss: ON (--balance_weight %g), Switch-Transformer-style '
              'load-balancing auxiliary loss over the %d fixed centers\' top-%d vertex '
              'candidates -- see modules/vertex_balance_loss.py'
              % (args.balance_weight, num_centers, args.k_vertices_per_pixel))

    if args.lora_w_rank > 0:
        # LORA-W (2026-09-17, Tal): freeze the whole phase-1 encoder, train only a rank-r update B A on
        # the chosen Linear layers (modules/lora.py). B starts at 0, so step 0 == phase-1 exactly.
        wrapped = apply_lora_w(encoder, args.lora_w_rank, args.lora_w_layers)
        for m in encoder.modules():                                     # 2026-11-18 (Tal): train with W + alpha * BA
            if hasattr(m, 'lora_A'):
                m.alpha = args.lora_w_train_alpha
        trainable = [p for p in encoder.parameters() if p.requires_grad]
        with torch.no_grad():
            d0 = feature_drift(encoder(vertices), phase1_features)
        print('  LORA-W: rank %d on mlp layers %s (%s), %d trainable params, lr %g, step-0 drift %.6f'
              % (args.lora_w_rank, wrapped, args.lora_w_layers, sum(p.numel() for p in trainable),
                 args.lora_w_lr, d0))
        optimizer = torch.optim.Adam(trainable, args.lora_w_lr, eps=args.adam_eps)
    else:
        optimizer = torch.optim.Adam(encoder.parameters(), args.lr, eps=args.adam_eps)
    if mu_log_scale is not None:
        # its own param group: the scale is one number (or 17), not a feature map, and it has to be
        # free to move much faster than the encoder or it will not arrive inside 300 steps
        optimizer.add_param_group({'params': [mu_log_scale], 'lr': args.mu_lr})
    if mu_aniso is not None:
        optimizer.add_param_group({'params': [mu_aniso], 'lr': 0.0 if args.stageA_fixed else args.mu_lr})
    os.makedirs(args.out_dir, exist_ok=True)

    losses = []
    drifts = []
    # See the note at the top of train(): decouples the per-step neighbour stream from the
    # amount of RNG the setup above consumed.
    torch.manual_seed(args.train_seed + 1)

    for step in range(1, args.num_iters + 1):
        optimizer.zero_grad()

        if args.resample_centers:
            # Fresh random subset of the candidate pool every step -- unlike the fixed-once
            # `coords` the non-resample branch below keeps for the whole run. Neighbours are
            # unaffected: sample_in_segment_neighbors/sample_out_segment_neighbors already draw
            # from the FULL on-object pixel set regardless of which centers are active this
            # step (see geodesic_distance_2d_lookup -- the table's columns already cover every
            # on-object pixel, only the ROWS are restricted to a candidate set).
            step_center_idx = torch.randperm(num_candidates)[:args.num_center_pixels]
            coords = candidate_coords[step_center_idx]
            segment_ids = candidate_segment_ids[step_center_idx]
            if args.geodesic:
                # Cheap fancy-indexing into the already-loaded pool table -- no new geodesic
                # computation, same as the non-resample path's one-time row selection.
                geo_table_2d_center_rows = geo_table_2d[step_center_idx]
        elif args.geodesic:
            geo_table_2d_center_rows = geo_table_2d

        switch_global = (args.mu_scope == 'global_then_segment_aniso' and step < args.mu_switch_step)
        if args.mu_scope == 'global_then_segment_aniso' and step == args.mu_switch_step:
            if not args.no_step_checkpoints or args.save_stageA_end:
                # END OF STAGE A (2026-10-06, Tal: back-projection after stage 1): the encoder and the global ellipse
                # exactly as stage A left them, before the first stage-B step. Same keys as a step checkpoint.
                torch.save({'encoder_state_dict': (merged_state_dict(encoder, args.lora_w_train_alpha) if args.lora_w_rank > 0
                                                   else encoder.state_dict()),
                            'lora_state': lora_state(encoder) if args.lora_w_rank > 0 else None,
                            'fourier_basis': get_fourier_basis(encoder), 'step': step - 1},
                           os.path.join(args.out_dir, 'encoder_checkpoint_stageA_end.pth'))
                _maj, _min, _ang = aniso_axes(mu_aniso)
                torch.save({'mu_aniso': mu_aniso.detach().cpu(), 'major': _maj.cpu(), 'minor': _min.cpu(),
                            'major_angle_deg': _ang.cpu(), 'present_groups': torch.unique(segment_ids).cpu(),
                            'scope': args.mu_scope, 'grid': None, 'grid_bbox': None},
                           os.path.join(args.out_dir, 'mu_aniso_stageA_end.pth'))
            with torch.no_grad():
                mu_aniso[:-1] = mu_aniso[-1]          # stage B starts every segment at the global ellipse
                if args.mu_aniso_fixed_path is not None:
                    # HAND-MADE ellipses (Tal, 2026-09-28; analysis/make_manual_mu_aniso.py): stage B uses them FROZEN.
                    # Their Adam moments are 0 (rows unused in stage A) and the hook zeroes their grads -> no update.
                    fixed = torch.load(args.mu_aniso_fixed_path, map_location='cpu')['mu_aniso'].float()
                    if args.switch_hybrid and fixed.shape[0] == mu_aniso.shape[0]:
                        # stage B = HYBRID with hand-made per-seg rows AND a hand-made global (cross-seg) row, all frozen.
                        # lr -> 0 too: the global row carries Adam moments from stage A and would keep drifting on zero grads.
                        mu_aniso[:] = fixed.to(device)
                        for _g in optimizer.param_groups:
                            if any(_p is mu_aniso for _p in _g['params']): _g['lr'] = 0.0
                        mu_aniso.register_hook(lambda g: torch.zeros_like(g))
                        fixed = None
                        print('  step %d: stage-B HYBRID ellipses (segments + global) LOADED + FROZEN from %s' % (step, args.mu_aniso_fixed_path))
                if args.mu_aniso_fixed_path is not None and fixed is not None:
                    if fixed.shape[0] != mu_aniso.shape[0] - 1:
                        raise SystemExit('--mu_aniso_fixed_path has %d rows, run has %d segments' % (fixed.shape[0], mu_aniso.shape[0] - 1))
                    mu_aniso[:-1] = fixed.to(device)
                    _frz = torch.ones_like(mu_aniso); _frz[:-1] = 0
                    mu_aniso.register_hook(lambda g: g * _frz)
                    print('  step %d: stage-B ellipses LOADED + FROZEN from %s' % (step, args.mu_aniso_fixed_path))
                if args.mu_fix_seg_circle:
                    # ONE segment's ellipse fixed to a circle at the switch, the rest keep learning (Tal, 2026-09-29).
                    # The row was unused in stage A -> zero Adam moments; the masked grad keeps it exactly fixed.
                    _fixmask = torch.ones_like(mu_aniso)
                    for _spec in args.mu_fix_seg_circle:
                        _sg, _v = _spec.split(':'); _sg = int(_sg); _v = float(_v)
                        mu_aniso[_sg] = torch.tensor([_v, _v, 1.0], device=mu_aniso.device).log() * torch.tensor([1.0, 1.0, 0.0], device=mu_aniso.device)
                        _fixmask[_sg] = 0
                        print('  step %d: seg %d ellipse FIXED to circle %g (rest learned)' % (step, _sg, _v))
                    mu_aniso.register_hook(lambda g: g * _fixmask)
            print('  step %d: SWITCH global -> per-segment ellipses (init = global %s), neighbours %d in + %d out'
                  % (step, [round(x, 3) for x in mu_aniso[-1].tolist()], args.switch_nin, args.switch_nout))
        n_in, n_out = ((args.switch_nin, args.switch_nout)
                       if args.mu_scope == 'global_then_segment_aniso' and not switch_global
                       else (args.num_neighbors_in_segment, args.num_neighbors_out_segment))
        if args.fixed_neighbors:
            neighbor_coords = fixed_neighbor_coords
        else:
            neighbor_coords_in = sample_in_segment_neighbors(
                coords, segment_ids, seg_idx, k=n_in)
            neighbor_coords_out = sample_out_segment_neighbors(
                coords, segment_ids, seg_idx, k=n_out,
                max_retries=args.out_segment_max_retries)
            neighbor_coords = torch.cat([neighbor_coords_in, neighbor_coords_out], dim=1)
            if args.mu_scope == 'dual_global_local_aniso':
                neighbor_coords = torch.cat([neighbor_coords, sample_in_segment_neighbors(
                    coords, segment_ids, seg_idx, k=args.dual_local_nin)], dim=1)

        # Same flat-batch pattern as train_mapping_loss.py: centers are rows
        # [:n], neighbour (i, j) is row n + i*num_neighbors + j.
        all_coords = torch.cat([coords, neighbor_coords.reshape(-1, 2)], dim=0)
        pixel_features = index_pixel_features(all_pixel_features, all_coords)

        # Live encoder output, NOT the saved pred_f.pth -- see
        # train_mapping_loss.py's identical comment for why.
        vertex_features = encoder(vertices)

        if args.geodesic:
            # return_topk=True: geodesic distance needs each pixel's own top-K vertex
            # candidates/weights, not the already-collapsed (generally off-surface) point --
            # see modules/relational_loss.py's geodesic-variant docstring for why the collapsed
            # point can't be used here the way it is for Euclidean distance.
            # soft_points (the collapsed Σ w·v point) is unused by the geodesic distance, but
            # --rkd_spatial_angle3_weight needs it: Euclidean angles are measured between these points.
            soft_points, topk_idx, weights = soft_map_to_vertices(
                pixel_features, vertex_features, vertices, args.k_vertices_per_pixel,
                return_topk=True, temperature=args.temperature)

            center_topk_idx = topk_idx[:num_centers]
            center_weights = weights[:num_centers]
            neighbor_topk_idx = topk_idx[num_centers:].view(
                num_centers, num_neighbors, args.k_vertices_per_pixel)
            neighbor_weights = weights[num_centers:].view(
                num_centers, num_neighbors, args.k_vertices_per_pixel)

            # --xseg_feat_mode: only the IN-segment prefix of the neighbour axis enters the spatial term
            # (the axis is cat([in, out]); the cross-segment rest goes to xseg_feat_loss below).
            # Off: the full tensors, untouched, so every earlier run is bit-identical.
            if xseg_on:
                _nin = args.num_neighbors_in_segment
                sp_coords = neighbor_coords[:, :_nin]
                sp_topk_idx, sp_weights = neighbor_topk_idx[:, :_nin], neighbor_weights[:, :_nin]
            else:
                sp_coords, sp_topk_idx, sp_weights = neighbor_coords, neighbor_topk_idx, neighbor_weights
            if xseg_on and step == 1:
                # the split is by POSITION on the neighbour axis -- check it against the actual segments once
                _seg = torch.as_tensor(fine_segments).long()
                _cs = segment_ids.long().unsqueeze(1)
                _same = _seg[neighbor_coords[..., 0], neighbor_coords[..., 1]] == _cs
                print('  XSEG check, step 1: same segment as the centre -- in-segment slice %.4f (must be 1), '
                      'cross-segment slice %.4f (must be 0)'
                      % (_same[:, :_nin].float().mean().item(), _same[:, _nin:].float().mean().item()))
            _rl = rkd_spatial_dist_loss(
                center_topk_idx, center_weights, sp_topk_idx, sp_weights,
                sp_coords, geo_table_3d, geo_table_2d_center_rows, pixel_to_node,
                mu_3D_reference=mu_3D_reference, mu_2D_reference=mu_2D_reference,
                mu_3d_scale=(args.mu_3d_scale if args.mu_mode == 'fixed' else
                             'optimal' if args.mu_mode == 'optimal' else
                             aniso_scale_from_params(grid_center_params(mu_aniso, coords, mu_grid_bbox,
                                                                        args.mu_grid), coords, sp_coords)
                             if args.mu_scope == 'grid_aniso' else
                             hybrid_aniso_mu_scale(mu_aniso, coords, sp_coords, mu_groups,
                                                   mu_seg_map[sp_coords[..., 0].to(device),
                                                              sp_coords[..., 1].to(device)])
                             if args.mu_scope == 'segment_aniso_xglobal' else
                             hybrid_aniso_mu_scale(mu_aniso, coords, sp_coords, mu_groups,
                                                   mu_seg_map[sp_coords[..., 0].to(device),
                                                              sp_coords[..., 1].to(device)])
                             if args.mu_scope == 'global_then_segment_aniso' and args.switch_hybrid and not switch_global else
                             dual_aniso_mu_scale(mu_aniso, coords, sp_coords, mu_groups,
                                                 args.num_neighbors_in_segment + args.num_neighbors_out_segment)
                             if args.mu_scope == 'dual_global_local_aniso' else
                             switch_aniso_mu_scale(mu_aniso, coords, sp_coords, mu_groups, switch_global)
                             if args.mu_scope == 'global_then_segment_aniso' else
                             aniso_mu_scale(mu_aniso, coords, sp_coords, mu_groups)
                             if mu_aniso is not None else mu_log_scale.exp()),
                mu_groups=mu_groups, mu_n_groups=mu_n_groups,
                mu_neighbor_groups=(None if mu_seg_map is None else
                                    mu_seg_map[sp_coords[..., 0].to(device),
                                               sp_coords[..., 1].to(device)]),
                mu_fit_space=args.mu_fit_space,
                return_mu_scale=(args.mu_mode != 'fixed'),
                huber_delta=args.huber_delta,
                return_residuals=(args.dump_residuals and step == 1))
            if args.mu_mode != 'fixed':
                loss, mu_2D, mu_3D_live, mu_scale_step = _rl
                _rl = (loss, mu_2D, mu_3D_live)
            if args.dump_residuals and step == 1:
                loss, mu_2D, mu_3D_live, residuals = _rl
                # --dump_residuals (2026-09-09): --huber_delta is a transition point on the
                # per-pair residual norm_d_3D - norm_d_2D, so picking it without knowing that
                # quantity's scale is guessing. Both distances are divided by a geodesic
                # diameter, so they live in [0, 1]; if the residuals sit orders of magnitude
                # below delta, Huber never leaves its quadratic branch and the loss is plain MSE.
                a = residuals.abs().flatten().float().cpu()
                qs = [50, 75, 90, 95, 99, 99.9]
                vals = torch.quantile(a, torch.tensor([q / 100.0 for q in qs]))
                print('--- residual |norm_d_3D - norm_d_2D| at step 1, n=%d pairs' % a.numel())
                print('    mean %.5f  rms %.5f  max %.5f'
                      % (a.mean().item(), a.pow(2).mean().sqrt().item(), a.max().item()))
                for q, v in zip(qs, vals.tolist()):
                    print('    p%-5s %.5f' % (q, v))
                for d in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0):
                    print('    delta=%-5g clips %6.2f%% of pairs' % (d, 100.0 * (a > d).float().mean().item()))
                print('--- (--dump_residuals: diagnostic only, stopping before backward)')
                return
            loss, mu_2D, mu_3D_live = _rl
        else:
            # return_topk=True even here (unused for relational_loss itself, which only needs
            # `points`): --balance_weight needs the same per-pixel top-K weights the geodesic
            # branch above already gets for free, and requesting them costs nothing extra --
            # soft_map_to_vertices computes topk_idx/weights internally either way, return_topk
            # only controls whether they're handed back.
            soft_points, topk_idx, weights = soft_map_to_vertices(
                pixel_features, vertex_features, vertices, args.k_vertices_per_pixel,
                return_topk=True, temperature=args.temperature)

            center_points = soft_points[:num_centers]
            neighbor_points = soft_points[num_centers:].view(num_centers, num_neighbors, 3)
            center_topk_idx = topk_idx[:num_centers]
            center_weights = weights[:num_centers]

            loss, mu_2D, mu_3D_live = relational_loss(
                center_points, neighbor_points, coords, neighbor_coords,
                mu_3D_reference=mu_3D_reference, mu_2D_reference=mu_2D_reference,
                distance_weight=args.distance_weight, mu_3d_scale=args.mu_3d_scale,
                huber_delta=args.huber_delta)

        loss = args.rkd_spatial_dist_weight * loss
        sdist_loss = loss  # the weighted rkd_spatial_dist term alone -- reference for --rkd_feat_angle2_balance

        if args.flip_weight > 0:
            # expected template geodesic between mirror(soft map of pixel (r, c)) and the soft map of pixel (r, W-1-c) of the flipped
            # image, over the template diameter; squared / 2 like the Huber's quadratic branch
            _fc = coords.clone(); _fc[:, 1] = all_pixel_features.shape[1] - 1 - _fc[:, 1]
            _, _fti, _fw = soft_map_to_vertices(index_pixel_features(flip_pixel_features, _fc), vertex_features, vertices,
                                                args.k_vertices_per_pixel, return_topk=True, temperature=args.temperature)
            _ci, _cw = topk_idx[:num_centers], weights[:num_centers]
            _g = geo_table_3d[flip_mirror[_ci].unsqueeze(2), _fti.unsqueeze(1)]                    # [n, K, K]
            _dflip = (_g * _cw.unsqueeze(2) * _fw.unsqueeze(1)).sum((1, 2)) / mu_3D_reference
            flip_loss = 0.5 * (_dflip ** 2).mean()
            loss = loss + args.flip_weight * flip_loss
            if step == 1 or step % args.checkpoint_every == 0:
                print('    flip term: mean d(mirror(I), flip(I)) %.4f of the diameter, weighted loss %.6f (spatial %.6f)'
                      % (_dflip.mean().item(), args.flip_weight * flip_loss.item(), sdist_loss.item()))

        # --- XSEG cross-segment feature term (Tal, 2026-10-19) ----------------------------------------------
        # The cross-segment suffix of the neighbour axis, which rkd_spatial_dist no longer sees. 'off' skips
        # the block, so every earlier run is bit-identical (no RNG is consumed here either way).
        xseg_raw = xseg_gap = xseg_teacher = xseg_student = float('nan')
        if xseg_on:
            _nin = args.num_neighbors_in_segment
            _xargs = (pixel_features[:num_centers],
                      pixel_features[num_centers:].view(num_centers, num_neighbors, -1)[:, _nin:],
                      center_topk_idx, center_weights, neighbor_topk_idx[:, _nin:], neighbor_weights[:, _nin:],
                      vertex_features, frozen_vertex_unit)
            if args.xseg_feat_balance and step == args.xseg_feat_balance_step:
                # Same rule as every other term: under Adam only the RATIO of gradient norms matters.
                params = [p for p in encoder.parameters() if p.requires_grad]
                def _gnx(t):
                    gs = torch.autograd.grad(t, params, retain_graph=True, allow_unused=True)
                    return torch.sqrt(sum((g.float() ** 2).sum() for g in gs if g is not None)).item()
                g_sd = _gnx(sdist_loss)
                print('--- xseg_feat balance at step %d (%d in-segment pairs -> spatial, %d cross-segment -> feature)'
                      % (step, _nin, args.num_neighbors_out_segment))
                print('    rkd_spatial_dist (in-seg) : loss %.6e  grad norm %.4e' % (sdist_loss.item(), g_sd))
                for _m in XSEG_FEAT_MODES:
                    _l, _gap, _t, _s = xseg_feat_loss(*_xargs, mode=_m, huber_delta=args.huber_delta)
                    g_x = _gnx(_l)
                    print('    xseg_feat %-6s          : loss %.6e  grad norm %.4e  |gap| %.4f  teacher %.4f  student %.4f'
                          % (_m, _l.item(), g_x, _gap, _t, _s))
                    for r in (1.0, 3.0, 10.0):
                        print('        --xseg_feat_weight at 1/%g of rkd_spatial_dist: %.4e'
                              % (r, g_sd / (r * max(g_x, 1e-30))))
                    print('XSEG_WEIGHT mode=%s weight_equal=%.4e' % (_m, g_sd / max(g_x, 1e-30)))   # read by scripts/run_xseg_horse.sh
                print('--- (--xseg_feat_balance: diagnostic only, stopping before backward)')
                return
            x_loss, xseg_gap, xseg_teacher, xseg_student = xseg_feat_loss(
                *_xargs, mode=args.xseg_feat_mode, huber_delta=args.huber_delta)
            xseg_raw = x_loss.item()
            if args.xseg_feat_weight > 0.0:
                loss = loss + args.xseg_feat_weight * x_loss

        # --- rkd_spatial_angle3 (added 2026-09-15 as ANGLE-SPATIAL) ------------------------------------------------
        # RKD's angle term in the SPATIAL domain, EUCLIDEAN angles (image-plane rays vs chords
        # between the soft-mapped 3D points) -- see rkd_spatial_angle3_loss(). Weight 0.0 skips the
        # block, so every earlier run is bit-identical.
        sang_raw = sang_gap = sang_valid = float('nan')
        if args.rkd_spatial_angle3_weight > 0.0 or args.rkd_spatial_angle3_balance:
            if not args.geodesic:
                raise SystemExit('--rkd_spatial_angle3_weight is only wired into the --geodesic branch')
            sang_loss, sang_gap, sang_valid = rkd_spatial_angle3_loss(
                soft_points[:num_centers],
                soft_points[num_centers:].view(num_centers, num_neighbors, 3),
                coords, neighbor_coords, min_ray_px=args.rkd_spatial_angle3_min_ray_px,
                huber_delta=args.huber_delta)
            sang_raw = sang_loss.item()
            if args.rkd_spatial_angle3_balance:
                # Same rule as every other term: under Adam only the RATIO of gradient norms matters.
                params = [p for p in encoder.parameters() if p.requires_grad]
                def _gn(t):
                    gs = torch.autograd.grad(t, params, retain_graph=True, allow_unused=True)
                    return torch.sqrt(sum((g.float() ** 2).sum() for g in gs if g is not None)).item()
                g_rel, g_ang = _gn(loss), _gn(sang_loss)
                print('--- rkd_spatial_angle3 balance (Euclidean angles, min ray %g px)'
                      % args.rkd_spatial_angle3_min_ray_px)
                print('    rkd_spatial_dist  : loss %.6e  grad norm %.4e' % (loss.item(), g_rel))
                print('    rkd_spatial_angle3: loss %.6e  grad norm %.4e  |cos gap| %.4f  valid triplets %.3f'
                      % (sang_raw, g_ang, sang_gap, sang_valid))
                for r in (1.0, 3.0, 10.0):
                    print('    rkd_spatial_angle3_weight at 1/%g of rkd_spatial_dist: %.4e'
                          % (r, g_rel / (r * max(g_ang, 1e-30))))
                print('--- (--rkd_spatial_angle3_balance: diagnostic only, stopping before backward)')
                return
            loss = loss + args.rkd_spatial_angle3_weight * sang_loss

        # --- ZS anchor (added 2026-09-10)---------------------------------------------------
        # The only ABSOLUTE term in phase-2: CE of the student's distribution over all vertices
        # against the frozen phase-1 one, on the same center pixels. Weight 0.0 skips the block,
        # so every pre-existing run is bit-identical (no RNG is consumed here either way).
        anc_kl = anc_agree = float('nan')
        # --rkd_feat_angle2_balance reuses --anchor_balance_from only to LOAD the step-25 state; the anchor's
        # own balance diagnostic (which returns) must then be skipped so the feature block is reached.
        _anchor_diag = args.anchor_balance_from and not args.rkd_feat_angle2_balance
        if args.anchor_weight > 0.0 or _anchor_diag:
            anc_loss, anc_kl, anc_agree = anchor_loss(
                pixel_features[:num_centers], vertex_features, phase1_features,
                args.anchor_temperature, hard=args.anchor_hard)
            if _anchor_diag:
                # Under Adam a constant factor on the WHOLE loss cancels, but the RATIO between
                # two terms does not -- so lambda is chosen where the two gradient norms match.
                params = [p for p in encoder.parameters() if p.requires_grad]
                def _gnorm(t):
                    gs = torch.autograd.grad(t, params, retain_graph=True, allow_unused=True)
                    return torch.sqrt(sum((g.float() ** 2).sum() for g in gs if g is not None)).item()
                g_rel, g_anc = _gnorm(loss), _gnorm(anc_loss)
                print('--- anchor balance (%s target, T=%g)' % (
                    'hard' if args.anchor_hard else 'soft', args.anchor_temperature))
                print('    relational: loss %.6e  grad norm %.4e' % (loss.item(), g_rel))
                print('    anchor    : loss %.6e  grad norm %.4e  KL %.4e  top1 agree %.3f'
                      % (anc_loss.item(), g_anc, anc_kl, anc_agree))
                print('    lambda at equal grad norms: %.4e' % (g_rel / max(g_anc, 1e-30)))
                if args.cyc_weight > 0.0 and args.cyc_v2:
                    # Cycle rides next to the anchor at SHIC's ratio (beta/alpha = 0.002/0.1 = 1/50):
                    # pick cyc_weight so its gradient norm is 1/50 of the WEIGHTED anchor's.
                    c_loss, _, c_refs = _cyc_v2(pixel_features[:num_centers], vertex_features)
                    g_cyc = _gnorm(c_loss)
                    print('    cycle v2  : loss %.6e  grad norm %.4e  (T=%g, argmax refs %d)'
                          % (c_loss.item(), g_cyc, args.cyc_temperature, c_refs))
                    print('    cyc_weight at 1/50 of anchor (lambda=%g): %.4e'
                          % (args.anchor_weight, args.anchor_weight * g_anc / (50.0 * max(g_cyc, 1e-30))))
                if args.dist_balance:
                    # L_dist rides next to the anchor at the same kind of ratio as the cycle.
                    d_loss, d_tail, d_agree, _ = dist_loss(
                        pixel_features[:num_centers], vertex_features, phase1_features,
                        geo_table_3d, geo_diag_3d, args.dist_temperature,
                        soft_target_temperature=args.dist_soft_target_temperature)
                    g_dist = _gnorm(d_loss)
                    print('    L_dist    : loss %.6e  grad norm %.4e  (T_dist=%g, tail>0.2D %.3f, '
                          'zs_top1 %.3f)'
                          % (d_loss.item(), g_dist, args.dist_temperature, d_tail, d_agree))
                    for r in (10.0, 50.0):
                        print('    dist_weight at 1/%g of anchor (lambda=%g): %.4e'
                              % (r, args.anchor_weight,
                                 args.anchor_weight * g_anc / (r * max(g_dist, 1e-30))))
                print('--- (--anchor_balance_from: diagnostic only, stopping before backward)')
                return
            loss = loss + args.anchor_weight * anc_loss

        # --- SHIC L_dist (added 2026-09-12) --------------------------------------------------
        # The METRIC companion to the anchor: E_p[ geodesic distance to the ZS argmax ]. The
        # anchor's CE is blind to WHERE the mass it dislikes sits; this term is blind to how
        # peaked p is and sees only that. See modules/dist_loss.py for the full argument.
        # x~ is fixed across steps whenever the centers are (i.e. unless --resample_centers),
        # so it is computed once and cached.
        dist_tail = dist_agree = float('nan')
        if args.dist_weight > 0.0:
            dst_loss, dist_tail, dist_agree, dist_target_idx = dist_loss(
                pixel_features[:num_centers], vertex_features, phase1_features,
                geo_table_3d, geo_diag_3d, args.dist_temperature,
                target_idx=None if args.resample_centers else dist_target_idx,
                soft_target_temperature=args.dist_soft_target_temperature)
            loss = loss + args.dist_weight * dst_loss

        # --- feature-space RKD (added 2026-08-28) -------------------------------------------
        # Two additive terms on the feature dimension, on top of the geometric relational loss
        # above: total = alpha*relational + beta*RKD-D(features) + gamma*RKD-A(features).
        # Both default to weight 0.0, so every pre-existing run is bit-identical.
        # Computed whenever either weight is on OR --log_feature_terms is set, so their raw
        # magnitudes can be read off a run that does not yet use them.
        feat_dist_raw = feat_angle_raw = cos_gap = float('nan')
        mu_img_live = mu_msh_live = float('nan')
        if (args.rkd_feat_dist_weight > 0.0 or args.rkd_feat_angle3_weight > 0.0
            or args.rkd_feat_angle2_weight > 0.0 or args.log_feature_terms
            or args.rkd_feat_angle2_balance):
            img_center = pixel_features[:num_centers]
            img_neighbors = pixel_features[num_centers:].view(num_centers, num_neighbors, -1)
            # --feat_detach_weights (2026-08-29): THE CIRCULARITY TEST. `weights` come from a softmax
            # over image<->vertex feature similarity, i.e. from the very quantity this loss is trying
            # to fix. Left attached, the loss has two ways down: genuinely improve vertex_features
            # (what we want), or just reshuffle/sharpen the weights so the weighted averages land
            # where it wants (what we do not). Detaching blocks the second path, so the loss can only
            # fall by moving features. Only the FEATURE loss is affected -- the geometric relational
            # loss uses center_points/neighbor_points and is untouched. The other soft_feature() call
            # (measure_feature_mu) is under no_grad, so it is unaffected either way.
            if args.feat_student_mode == 'argmax':
                # k=1: no mixing at all, so --feat_detach_weights is irrelevant here (only the
                # argmax INDEX is taken from `weights`, and an index carries no gradient).
                msh_all = hard_feature(vertex_features, topk_idx, weights)
            else:
                # --feat_detach_features (2026-08-31, Tal): the MIRROR of --feat_detach_weights.
                # Detaching the F values leaves w as the only route to the encoder, which is exactly
                # the structure of the SPATIAL relational loss (its Sum w*X uses fixed vertex
                # POSITIONS, so it has no value path at all). The gradient still reaches the encoder,
                # because w is a softmax over f(i)*F computed from the live, undetached features.
                msh_all = soft_feature(
                    vertex_features.detach() if args.feat_detach_features else vertex_features,
                    topk_idx,
                    weights.detach() if args.feat_detach_weights else weights)
            msh_center = msh_all[:num_centers]
            msh_neighbors = msh_all[num_centers:].view(num_centers, num_neighbors, -1)

            fd_loss, mu_img_live, mu_msh_live = rkd_feat_dist_loss(
                img_center, img_neighbors, msh_center, msh_neighbors,
                mu_img_reference=mu_img_reference, mu_msh_reference=mu_msh_reference,
                huber_delta=args.huber_delta)
            fa_loss, cos_gap = rkd_feat_angle3_loss(
                img_center, img_neighbors, msh_center, msh_neighbors,
                huber_delta=args.huber_delta)
            # PAIRWISE (2-point) angle, Tal's variant 2026-09-04 -- cos(center, neighbour), one
            # per pair, no mu anywhere. See rkd_feat_angle2_loss' docstring for how it
            # differs from the 3-point fa_loss above. Always COMPUTED when the block runs (it is a
            # cheap [n,k] cosine) so its raw magnitude is logged even at weight 0 -- that is how the
            # weight gets chosen, rather than guessed.
            #
            # --rkd_feat_angle2_neighbors in_segment (Tal, 2026-09-04; old flag --feat_pair_angle_neighbors): use only the CLOSE
            # neighbours. The neighbour axis is built as cat([in_segment, out_segment], dim=1) (see
            # the sampling above), so the first --num_neighbors_in_segment entries ARE the close
            # ones and a plain prefix slice is exactly right. THIS SLICE APPLIES TO THE PAIR-ANGLE
            # TERM ONLY -- the geometric relational loss above still sees all 16, so the matched
            # control (the spatial-only run) stays a ONE-variable comparison.
            if args.rkd_feat_angle2_neighbors == 'in_segment':
                n_close = args.num_neighbors_in_segment
                pa_img_neighbors = img_neighbors[:, :n_close]
                pa_msh_neighbors = msh_neighbors[:, :n_close]
            else:
                pa_img_neighbors = img_neighbors
                pa_msh_neighbors = msh_neighbors
            fpa_loss, pair_cos_gap = rkd_feat_angle2_loss(
                img_center, pa_img_neighbors, msh_center, pa_msh_neighbors,
                huber_delta=args.huber_delta)
            feat_dist_raw = fd_loss.item()
            feat_angle_raw = fa_loss.item()
            feat_pair_angle_raw = fpa_loss.item()
            if args.rkd_feat_angle2_balance:
                # Same rule as every other term: under Adam only the RATIO of gradient norms matters.
                params = [p for p in encoder.parameters() if p.requires_grad]
                def _gn2(t):
                    gs = torch.autograd.grad(t, params, retain_graph=True, allow_unused=True)
                    return torch.sqrt(sum((g.float() ** 2).sum() for g in gs if g is not None)).item()
                g_sd, g_fa2 = _gn2(sdist_loss), _gn2(fpa_loss)
                print('--- rkd_feat_angle2 balance (neighbours: %s, student: %s)'
                      % (args.rkd_feat_angle2_neighbors, args.feat_student_mode))
                print('    rkd_spatial_dist : loss %.6e  grad norm %.4e' % (sdist_loss.item(), g_sd))
                print('    rkd_feat_angle2  : loss %.6e  grad norm %.4e  |cos gap| %.4f'
                      % (feat_pair_angle_raw, g_fa2, pair_cos_gap))
                for r in (1.0, 3.0, 10.0):
                    print('    rkd_feat_angle2_weight at 1/%g of rkd_spatial_dist: %.4e'
                          % (r, g_sd / (r * max(g_fa2, 1e-30))))
                print('--- (--rkd_feat_angle2_balance: diagnostic only, stopping before backward)')
                return

            if args.rkd_feat_dist_weight > 0.0:
                loss = loss + args.rkd_feat_dist_weight * fd_loss
            if args.rkd_feat_angle3_weight > 0.0:
                loss = loss + args.rkd_feat_angle3_weight * fa_loss
            if args.rkd_feat_angle2_weight > 0.0:
                loss = loss + args.rkd_feat_angle2_weight * fpa_loss

        if args.balance_weight > 0.0:
            bal_loss, bal_f, bal_P = vertex_balance_loss(
                center_topk_idx, center_weights, vertices.shape[0])
            loss = loss + args.balance_weight * bal_loss

        if args.cyc_weight > 0.0:
            if args.cyc_v2:
                # 2026-09-10: SHIC L_cyc + CSE temperature, all vertices -- modules/cycle_consistency_loss_v2.py
                cyc_loss, cyc_norm, cyc_num_verts = _cyc_v2(pixel_features[:num_centers], vertex_features)
            else:
                cyc_fn = cycle_consistency_loss_soft if args.cyc_soft else cycle_consistency_loss
                cyc_loss, cyc_norm, cyc_num_verts = cyc_fn(
                    pixel_features[:num_centers], vertex_features, vertices,
                    args.k_vertices_per_pixel, center_geo_dist)
            loss = loss + args.cyc_weight * cyc_loss

        if args.lora_w_l2 > 0.0:   # 2026-11-18 (Tal): L2-SP-style pull toward phase-1, so the matching reads at the trained alpha
            dw_l2 = sum((args.lora_w_train_alpha * m.delta_weight()).pow(2).sum()
                        for m in encoder.modules() if hasattr(m, 'lora_A'))
            loss = loss + args.lora_w_l2 * dw_l2

        loss.backward()

        if step == 1:
            grad_norm = torch.cat([p.grad.reshape(-1) for p in encoder.parameters()
                                   if p.grad is not None]).norm().item()
            print('step    1  total grad norm %.4e  peak GPU mem %.2f GB'
                  % (grad_norm, torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0.0))

        optimizer.step()
        losses.append(loss.item())

        if step % args.checkpoint_every == 0 or step == args.num_iters:
            with torch.no_grad():
                drift = feature_drift(encoder(vertices), phase1_features)
            drifts.append((step, drift))
            ref_2D_str = 'live' if mu_2D_reference is None else '%.2f' % mu_2D_reference
            ref_3D_str = 'live' if mu_3D_reference is None else '%.5f' % mu_3D_reference
            cyc_str = ('' if args.cyc_weight == 0.0 else
                      '  cyc=%.4f refs=%d/%d' % (cyc_norm, cyc_num_verts, vertices.shape[0]))
            bal_str = ('' if args.balance_weight == 0.0 else
                      '  bal=%.4f cov=%d/%d' % (bal_loss.item(), int((bal_f > 0).sum().item()),
                                                 vertices.shape[0]))
            feat_str = ('' if (args.rkd_feat_dist_weight == 0.0 and args.rkd_feat_angle3_weight == 0.0
                               and args.rkd_feat_angle2_weight == 0.0
                               and not args.log_feature_terms) else
                        '  feat_dist=%.6f feat_angle3=%.6f feat_angle2=%.6f (raw, unweighted; angle3_cos_gap=%.4f '
                        'angle2_cos_gap=%.4f mu_img_live=%.5f mu_msh_live=%.5f)'
                        % (feat_dist_raw, feat_angle_raw, feat_pair_angle_raw, cos_gap,
                           pair_cos_gap, mu_img_live, mu_msh_live))
            anc_str = ('' if args.anchor_weight == 0.0 else
                       '  anchor_KL=%.4f top1_agree=%.3f' % (anc_kl, anc_agree))
            dist_str = ('' if args.dist_weight == 0.0 else
                        '  L_dist=%.4f tail>0.2D=%.3f zs_top1=%.3f'
                        % (dst_loss.item(), dist_tail, dist_agree))
            # MU-LEARNED: report the fitted zoom. One number when global; min/median/max plus the
            # spread when per-segment, because the interesting question there is whether the
            # segments disagree (an isotropic scalar cannot fix it if they do).
            mu_str = ''
            if args.mu_mode != 'fixed':
                s = mu_scale_step.detach().flatten().float()
                mu_str = ('  mu_s=%.4f' % s.item() if s.numel() == 1 else
                          '  mu_s[min/med/max]=%.3f/%.3f/%.3f' %
                          (s.min().item(), s.median().item(), s.max().item()))
                if mu_aniso is not None:
                    # s above is per PAIR here; the per-segment ellipse is the readable summary
                    major, minor, _ = aniso_axes(mu_aniso)
                    ratio = major / minor
                    mu_str += ('  aniso major/minor[max]=%.3f (median %.3f)'
                               % (ratio.max().item(), ratio.median().item()))
            sang_str = ('' if args.rkd_spatial_angle3_weight == 0.0 else
                        '  spatial_angle3=%.5f (raw) cos_gap=%.4f valid=%.3f' % (sang_raw, sang_gap, sang_valid))
            if xseg_on:
                sang_str += ('  xseg_%s=%.6f (raw) |gap|=%.4f teacher=%.4f student=%.4f'
                             % (args.xseg_feat_mode, xseg_raw, xseg_gap, xseg_teacher, xseg_student))
            print('step %4d/%d  loss %.6f (mu_2D=%.3f mu_3D_live=%.5f, ref_2D=%s ref_3D=%s)%s%s%s%s%s%s%s  '
                  'drift(cos vs phase 1) %.4f'
                  % (step, args.num_iters, loss.item(), mu_2D, mu_3D_live,
                     ref_2D_str, ref_3D_str, cyc_str, bal_str, feat_str, anc_str, dist_str, mu_str,
                     sang_str, drift)
                  + ('  dw_l2 %.4f' % dw_l2.item() if args.lora_w_l2 > 0.0 else ''))

            if not args.no_step_checkpoints:
                torch.save({'encoder_state_dict': (merged_state_dict(encoder, args.lora_w_train_alpha) if args.lora_w_rank > 0
                                                   else encoder.state_dict()),
                            'lora_state': lora_state(encoder) if args.lora_w_rank > 0 else None,
                            'optimizer_state_dict': optimizer.state_dict(),
                            'fourier_basis': get_fourier_basis(encoder),
                            'step': step, 'loss': loss.item(), 'drift': drift,
                            'mu_aniso': None if mu_aniso is None else mu_aniso.detach().cpu()},  # per-step ellipse (probe_pair_loss.py)
                           os.path.join(args.out_dir, 'encoder_checkpoint_step%d.pth' % step))

            if args.stop_at_drift is not None and drift < args.stop_at_drift:
                print('drift %.4f fell below --stop_at_drift %.4f; stopping.'
                      % (drift, args.stop_at_drift))
                break

    # Final artifacts, mirroring phase 1's / train_mapping_loss.py's layout so
    # the analysis scripts can consume this checkpoint exactly like theirs.
    torch.save({'encoder_state_dict': (merged_state_dict(encoder, args.lora_w_train_alpha) if args.lora_w_rank > 0
                                               else encoder.state_dict()),
                        'lora_state': lora_state(encoder) if args.lora_w_rank > 0 else None,
                'optimizer_state_dict': optimizer.state_dict(),
                'fourier_basis': get_fourier_basis(encoder),
                'losses': losses, 'drifts': drifts},
               os.path.join(args.out_dir, 'encoder_checkpoint.pth'))
    with torch.no_grad():
        torch.save(encoder(vertices), os.path.join(args.out_dir, 'pred_f.pth'))
    if mu_log_scale is not None:
        # same {'mu_scale': [G]} format --mu_init_path reads, so a run's final mu can seed another
        torch.save({'mu_scale': mu_log_scale.detach().exp().cpu(),
                    'present_groups': torch.unique(segment_ids).cpu() if mu_n_groups > 1 else None},
                   os.path.join(args.out_dir, 'mu_scale.pth'))
    if mu_aniso is not None:
        major, minor, ang = aniso_axes(mu_aniso)
        torch.save({'mu_aniso': mu_aniso.detach().cpu(), 'major': major.cpu(), 'minor': minor.cpu(),
                    'major_angle_deg': ang.cpu(),
                    'present_groups': torch.unique(segment_ids).cpu(), 'scope': args.mu_scope,
                    'grid': args.mu_grid if args.mu_scope == 'grid_aniso' else None,
                    'grid_bbox': mu_grid_bbox if args.mu_scope == 'grid_aniso' else None},
                   os.path.join(args.out_dir, 'mu_aniso.pth'))
        print('mu_aniso per %s (major / minor / major-axis angle, 0 = vertical):'
              % ('grid node' if args.mu_scope == 'grid_aniso' else 'segment'))
        for g in (range(mu_n_groups) if args.mu_scope in ('grid_aniso', 'global_aniso')
                  else torch.unique(segment_ids).tolist()
                  + ([mu_n_groups - 1] if args.mu_scope in ('segment_aniso_xglobal', 'global_then_segment_aniso', 'dual_global_local_aniso') else [])):
            print('  seg %2d  %.3f / %.3f / %5.1f deg  (ratio %.3f)'
                  % (g, major[g].item(), minor[g].item(), ang[g].item(), (major[g] / minor[g]).item()))

    save_loss_plot(losses, drifts, args.checkpoint_every,
                   os.path.join(args.out_dir, 'relational_loss.png'))
    config = {k: v for k, v in vars(args).items()}
    config['input_sha256'] = {
        path: hash_input(path) for path in (args.object_mask_path, args.fine_seg_path,
                                            args.pix_dino_features_path)}
    with open(os.path.join(args.out_dir, 'run_config.json'), 'w') as f:
        json.dump(config, f, indent=2)

    print('\nloss %.6f -> %.6f over %d steps' % (losses[0], losses[-1], len(losses)))
    print('final drift vs phase 1: %.4f' % drifts[-1][1])
    print('saved to %s' % args.out_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # CANONICAL LOSS NAMES (Tal, 2026-09-15) -- one name per term everywhere (flags, logs, notes, run tags):
    #   rkd_spatial_dist   (tag sdist)   geodesic distance, 2 points       old: --relational_weight, "L_spatial"
    #   rkd_spatial_angle3 (tag sangle3) Euclidean angle at centre, 3 pts  old: --spatial_angle_*, ANGLE-SPATIAL
    #   rkd_feat_dist      (tag fdist)   feature distance, 2 points       old: --feat_dist_weight, featD
    #   rkd_feat_angle2    (tag fangle2) feature cosine, 2 points         old: --feat_pair_angle_*, featPA
    #   rkd_feat_angle3    (tag fangle3) feature angle at centre, 3 pts   old: --feat_angle_weight, featA, RKD-A
    # Run tags carry the weight after _w, e.g. sangle3_w8.83e-3. Old flags remain as aliases (same dest), so
    # old scripts and run_config.json files still reproduce.
    # Mesh / phase-1 checkpoint. The Encoder args MUST match the phase-1 run
    # (README step 2 used --model_type dino --width 1024 --n_classes 1024) or
    # the state dict will not load.
    parser.add_argument('--obj_path', type=str, default='./meshes/guitar.obj')
    parser.add_argument('--name', type=str, default='guitar')
    parser.add_argument('--init_encoder_dir', type=str,
                        default='./experiments/guitar/encoder_dino')
    parser.add_argument('--init_encoder_checkpoint', type=str, default=None,
                        help='defaults to <init_encoder_dir>/encoder_checkpoint.pth')
    parser.add_argument('--depth', type=int, default=4)
    parser.add_argument('--width', type=int, default=1024)
    parser.add_argument('--n_classes', type=int, default=1024)
    parser.add_argument('--positional_encoding', type=int, default=1)
    parser.add_argument('--sigma', type=float, default=5.0)

    # Data
    parser.add_argument('--object_mask_path', type=str, required=True,
                        help='coarse whole-object mask; center pixels are drawn from it')
    parser.add_argument('--fine_seg_path', type=str,
                        default='./demo/guitar/phase2/guitar_01_fine_segments.pth',
                        help='part-level label map from analysis/build_fine_segments.py; '
                             'defines the in-segment/out-of-segment split neighbours are '
                             'drawn from')
    parser.add_argument('--pix_dino_features_path', type=str, required=True)

    # Loss
    parser.add_argument('--num_center_pixels', type=int, default=2048,
                        help='pixels the loss is computed on per step. Sampled once, then '
                             'fixed for the whole run by default; with --resample_centers, a '
                             'fresh random subset of the candidate pool is drawn every step '
                             'instead, but the per-step COUNT is still this number.')
    parser.add_argument('--resample_centers', action='store_true',
                        help='2026-08-18: instead of sample_center_pixels\'s single fixed draw '
                             'of --num_center_pixels centers for the whole run, draw a fresh '
                             'random --num_center_pixels subset of a much larger candidate pool '
                             '(sample_grid_center_pixels, spacing --center_grid_stride) every '
                             'step -- the neighbours-side counterpart of this already existed '
                             '(resampled every step by default); this extends the same idea to '
                             'centers. Requires --geodesic and a --center_mode grid table '
                             '(analysis/build_geodesic_tables.py) at --geo_table_2d_path. Not '
                             'implemented with --cyc_weight>0 or --fixed_neighbors (see train()\'s '
                             'own checks for why). Off by default -- matches every existing '
                             'recipe/run byte-for-byte.')
    parser.add_argument('--center_grid_stride', type=int, default=3,
                        help='--resample_centers only: pixel spacing of the candidate-center '
                             'grid (sample_grid_center_pixels) -- must match the --center_mode '
                             'grid table\'s own --grid_stride it was built with '
                             '(analysis/build_geodesic_tables.py).')
    parser.add_argument('--rkd_feat_dist_weight', '--feat_dist_weight', type=float, default=0.0,
                        help='beta -- weight of the feature-space RKD-D term (distance between two '
                             'IMAGE features vs distance between the two corresponding MESH '
                             'features). 0.0 = off, and every pre-existing run is bit-identical at '
                             'the default. See modules/feature_rkd_loss.py.')
    parser.add_argument('--rkd_feat_angle3_weight', '--feat_angle_weight', type=float, default=0.0,
                        help='gamma -- weight of the feature-space RKD-A term (angle at a center, '
                             'formed with two of its neighbours, in image-feature space vs in '
                             'mesh-feature space). 0.0 = off. Needs no normalizer: a cosine is '
                             'already scale-free.')
    parser.add_argument('--rkd_feat_angle2_weight', '--feat_pair_angle_weight', type=float, default=0.0,
                        help='weight of the PAIRWISE (2-point) feature angle term, Tal 2026-09-04: '
                             'cos(center, neighbour) in image-feature space vs in mesh-feature '
                             'space, ONE per (center, neighbour) pair -- the same 2-point structure '
                             '--feat_dist_weight uses, with a cosine instead of a distance, so no '
                             'mu is needed anywhere. NOT the same as --feat_angle_weight, which is '
                             "the paper's 3-point angle between two NEIGHBOURS at the center. "
                             'Intended as an ADDITIVE term alongside the geometric relational loss. '
                             '0.0 = off, and the raw value is logged as feat_angle2 even at 0 so the '
                             'weight can be chosen from a measurement. Start an order of magnitude '
                             'below the 3-point term (gamma=0.2 collapsed a run).')
    parser.add_argument('--rkd_feat_angle2_neighbors', '--feat_pair_angle_neighbors', type=str, default='all',
                        choices=['all', 'in_segment'],
                        help="which neighbours the PAIRWISE angle term uses. 'all' (default) = "
                             'every sampled neighbour, i.e. in-segment + out-of-segment, and is '
                             "bit-identical to every run before 2026-09-04. 'in_segment' = only the "
                             'CLOSE ones (the first --num_neighbors_in_segment along the neighbour '
                             'axis, which is built as cat([in, out]) so the prefix is exactly the '
                             'in-segment set). Tal 2026-09-04. AFFECTS THE PAIR-ANGLE TERM ONLY -- '
                             'the geometric relational loss still uses every neighbour, so a run '
                             'with this flag differs from the spatial-only control by the '
                             'pair-angle term alone.')
    parser.add_argument('--rkd_feat_angle2_balance', action='store_true',
                        help='diagnostic: print the rkd_spatial_dist and rkd_feat_angle2 gradient norms and the '
                             'rkd_feat_angle2 weight at equal / 1/3 / 1/10, then stop before backward. Pair with '
                             '--anchor_balance_from <checkpoint> to measure on a drifted state (the anchor '
                             'diagnostic itself is skipped).')
    parser.add_argument('--feat_detach_weights', action='store_true',
                        help='CIRCULARITY TEST: detach the soft-map weights inside soft_feature(), '
                             'so the feature-RKD terms can only be reduced by changing vertex '
                             'features, not by sharpening the mapping that produced them. Default '
                             'OFF, so every pre-2026-08-29 run is reproduced exactly.')
    parser.add_argument('--feat_student_mode', type=str, default='soft',
                        choices=['soft', 'argmax'],
                        help="how the feature-RKD terms reach the mesh. 'soft' (default) is the "
                             'softmax-weighted average over k vertices, as every run before '
                             "2026-09-01. 'argmax' takes the single best-matching vertex's own "
                             'feature instead: no mixing, so there is no sharpening knob for the '
                             "loss to exploit and a pixel's whole gradient lands on one vertex. "
                             'See hard_feature() in modules/feature_rkd_loss.py.')
    parser.add_argument('--feat_detach_features', action='store_true',
                        help='detach the vertex FEATURES inside the soft student, so the feature-RKD '
                             'gradient reaches the encoder only through the soft-map weights -- the '
                             'mirror of --feat_detach_weights, and structurally what the spatial '
                             'relational loss does. Soft student only (argmax takes an index, which '
                             'carries no gradient, so detaching features there kills the term).')
    parser.add_argument('--feat_mu_stat', type=str, default='mean',
                        help="which statistic of the pair-distance distribution the FIXED feature "
                             "normalizer uses: 'mean' (default, the paper's), 'max' (each space by "
                             "its own largest pair distance), or 'pNN' e.g. 'p95'. max/p95 are much "
                             "larger than the mean, so the loss shrinks and beta must be rescaled.")
    parser.add_argument('--feat_mu_mode', type=str, default='fixed', choices=['fixed', 'live'],
                        help="normalizer for the RKD-D feature term. 'fixed' (default) measures mu "
                             'once from the phase-1 encoder and holds it, matching what the '
                             'geometric relational loss already does and for the same '
                             'anti-collapse reason. \'live\' recomputes it from each batch, which '
                             'is what the RKD paper itself does -- kept as a flag because Tal '
                             'explicitly wants to try it later.')
    parser.add_argument('--log_feature_terms', action='store_true',
                        help='compute and log the two feature-RKD terms unweighted even when both '
                             'weights are 0, to read off their natural magnitudes before choosing '
                             'beta/gamma. Costs one extra soft_feature + two losses per step and '
                             'does NOT affect the optimized loss.')
    # XSEG (Tal, 2026-10-19): split the pairs by kind. In-segment pairs (the first
    # --num_neighbors_in_segment along the neighbour axis) get rkd_spatial_dist; cross-segment pairs
    # (the rest) get xseg_feat_loss INSTEAD -- they leave the spatial term entirely. One stage, no switch.
    parser.add_argument('--xseg_feat_mode', type=str, default='off', choices=('off',) + XSEG_FEAT_MODES,
                        help="cross-segment pairs: 'off' (default) = every pair in rkd_spatial_dist, as every run "
                             "before. 'table' = feature RKD against the FROZEN phase-1 vertex features (gradient "
                             "through the match w only); 'wonly' = against the live features, F detached (w only); "
                             "'Fonly' = live features, w detached (F only). See xseg_feat_loss() in "
                             'modules/feature_rkd_loss.py. Needs --geodesic, --mu_scope segment_aniso and '
                             '--num_neighbors_out_segment > 0.')
    parser.add_argument('--xseg_feat_weight', type=float, default=0.0,
                        help='weight of the cross-segment feature term (calibrate with --xseg_feat_balance)')
    parser.add_argument('--xseg_feat_balance', action='store_true',
                        help='diagnostic: at step --xseg_feat_balance_step print the gradient norms of the weighted '
                             'in-segment rkd_spatial_dist and of the cross-segment feature term for ALL three modes, '
                             'and the weight at equal / 1/3 / 1/10, then stop before backward. Steps before it train '
                             'with --xseg_feat_weight (0 = in-segment spatial + cycle only).')
    parser.add_argument('--xseg_feat_balance_step', type=int, default=25,
                        help='step at which --xseg_feat_balance measures (default 25, as the earlier calibrations)')
    parser.add_argument('--temperature', type=float, default=1.0,
                         help='softmax temperature for soft_map_to_vertices (DPC Eq. 1-3). 1.0 = the '
                               'plain softmax every phase-2 run before 2026-08-25 trained with. NOTE: '
                               'the divide also scales the gradient reaching the encoder through the '
                               'weights by 1/T, so T=0.005 is a 200x gradient amplification on that '
                               'path, not just a sharper weighting -- treat lr accordingly.')
    parser.add_argument('--k_vertices_per_pixel', type=int, default=10,
                        help="mesh vertices each pixel is softly mapped onto, nearest in "
                             "FEATURE space (DPC's k_cc)")
    parser.add_argument('--num_neighbors_in_segment', type=int, default=8,
                        help='random pixels drawn from a center\'s own fine segment, '
                             'without replacement, resampled every step')
    parser.add_argument('--num_neighbors_out_segment', type=int, default=8,
                        help='random pixels drawn from outside a center\'s fine segment '
                             '(segment-exclusive), resampled every step')
    parser.add_argument('--out_segment_max_retries', type=int, default=10,
                        help='vectorized rejection-sampling rounds for out-of-segment '
                             'draws that land back in the center\'s own segment')
    parser.add_argument('--huber_delta', type=float, default=1.0,
                        help='Huber transition point on the normalized-distance residual; '
                             "1.0 is RKD's own fixed choice. Run --dump_residuals first: the "
                             'residuals here are ~0.02, so the default never leaves the '
                             'quadratic branch and the loss is effectively plain MSE.')
    parser.add_argument('--dump_residuals', action='store_true',
                        help='Diagnostic: at step 1, print the distribution of the per-pair '
                             'residual --huber_delta is a threshold on, then exit without '
                             'training. Geodesic branch only. Writes nothing.')
    parser.add_argument('--anchor_weight', type=float, default=0.0,
                        help='2026-09-10: weight of the ZS anchor, CE of the student distribution '
                             'over ALL vertices against the frozen phase-1 one (modules/anchor_loss.py, '
                             'structure from DensePose-CSE soft_embed.py). 0 = off, bit-identical.')
    parser.add_argument('--anchor_temperature', type=float, default=0.01,
                        help='T for both q_ZS and p. At T=1 q over 3886 vertices is ~uniform '
                             '(measured 2026-09-10); 0.01 = ~75 effective vertices.')
    parser.add_argument('--anchor_hard', action='store_true',
                        help='one-hot argmax target instead of soft q_ZS -- SHIC\'s L_pseudo, the control arm')
    parser.add_argument('--anchor_balance_from', type=str, default=None,
                        help='Diagnostic: load this phase-2 step checkpoint, print the gradient norms '
                             'of the relational and anchor terms and the lambda that equalizes them, '
                             'then exit. Needed because the soft anchor gradient is 0 at phase-1.')
    parser.add_argument('--dist_weight', type=float, default=0.0,
                        help='2026-09-12: weight of SHIC L_dist = sum_x p(x|u) d_geo(x, x~)/D, with a HARD '
                             'x~ = argmax q_ZS (modules/dist_loss.py). The METRIC term the anchor is blind '
                             'to: the anchor CE gives zero pull to a vertex q dislikes no matter how far '
                             'away it is. 0 = off, bit-identical.')
    parser.add_argument('--dist_temperature', type=float, default=1.0,
                        help='T for p inside L_dist. SEPARATE from --anchor_temperature on purpose: at '
                             'T=0.01 p is ~75 vertices and L_dist only re-ranks inside the anchor blob; at '
                             'T=1 the mass spans all 3886, which is where the far leak lives.')
    parser.add_argument('--dist_soft_target_temperature', type=float, default=None,
                        help='2026-09-13: SOFT L_dist target. None (default) = hard x~ = argmax q_ZS, '
                             'bit-identical. Otherwise d(x) = E_{y~q_ZS}[d_geo(x,y)]/D with q_ZS at this T; '
                             'minimizer = geodesic median of q, which only departs from x~ at T >= ~0.05 '
                             '(analysis/soft_dist_median_check.py).')
    parser.add_argument('--dist_balance', action='store_true',
                        help='Diagnostic, used with --anchor_balance_from: also print L_dist\'s gradient '
                             'norm and the gamma that puts it at 1/10 and 1/50 of the WEIGHTED anchor '
                             '(--anchor_weight), the same way cyc_weight is picked. Unlike the anchor, '
                             'L_dist\'s gradient is nonzero at phase-1, but the anchor it is being sized '
                             'against is not, so the same step checkpoint is used.')
    parser.add_argument('--cyc_v2', action='store_true',
                        help='2026-09-10: cycle loss v2 (modules/cycle_consistency_loss_v2.py) -- SHIC L_cyc '
                             'over ALL vertices with a temperature on both legs (CSE). Needs --cyc_weight > 0.')
    parser.add_argument('--cyc_temperature', type=float, default=0.05,
                        help='T for both legs of --cyc_v2. 0.05 = CSE cycle_pix2shape default.')
    parser.add_argument('--cyc_return_all_pixels', action='store_true',
                        help='--cyc_v2 return leg over ALL mask pixels (SHIC L_cyc as written) instead of '
                             'the 2048 centers. d(u,v) comes straight from the 2D table columns.')
    parser.add_argument('--cyc_return_stride', type=int, default=1,
                        help='2026-09-13, with --cyc_return_all_pixels: return leg only on mask pixels with '
                             'row %% s == 0 and col %% s == 0 (s=5: 212k -> ~8.5k). Distances stay exact '
                             '(column subset). 1 = all pixels, bit-identical.')
    parser.add_argument('--mu_3d_reference_samples', type=int, default=5,
                        help='independent random neighbour draws averaged together to '
                             'measure the FIXED mu_3D normalizer from the phase-1 encoder, '
                             'before training starts -- see measure_mu_3D_reference. Ignored '
                             'when --live_mu_3d is set.')
    parser.add_argument('--live_mu_3d', action='store_true',
                        help='2026-08-11 A/B test, axis 1: normalize d_3D by THIS STEP\'s own '
                             'live mean (the original, pre-2026-08-10-fix behavior) instead of '
                             'a fixed reference measured once from the phase-1 encoder. Off by '
                             'default (matches the verified-safe 2026-08-10 fix).')
    parser.add_argument('--fixed_neighbors', action='store_true',
                        help='2026-08-11 A/B test, axis 2: sample each center\'s in-segment/'
                             'out-of-segment neighbours ONCE, before training, and reuse them '
                             'every step, instead of resampling every step. Off by default '
                             '(matches the verified-safe 2026-08-10 fix).')
    parser.add_argument('--bbox_norm', action='store_true',
                        help='Normalize BOTH d_2D and d_3D by a FIXED bounding-box diagonal '
                             '(d_2D by the coarse mask\'s own pixel-space bbox diagonal, d_3D '
                             'by the mesh\'s own vertex bbox diagonal), instead of any '
                             'mean-of-sampled-pairs statistic (live or fixed-reference). '
                             'Both computed once from the object\'s geometry alone, before '
                             'training -- unlike a sampled mean, immune to the imbalance in '
                             'which segments the 2048 centers happen to land in (measured: '
                             'body 66.5%%, neck 16.7%%, headstock only 4.5%% of centers). '
                             'Standard cross-domain-scale convention (e.g. NOCS\'s unit-cube '
                             'canonicalization). Mutually exclusive with --live_mu_3d.')
    parser.add_argument('--geodesic', action='store_true',
                        help='Both d_2D and d_3D become GEODESIC distances instead of Euclidean '
                             '-- 2D constrained to travel through the object mask (any segment, '
                             'not just the center\'s own), 3D constrained to the mesh surface. '
                             'Requires --geo_table_3d_path/--geo_table_2d_path from '
                             'analysis/build_geodesic_tables.py. Normalizes by GEODESIC diameters '
                             '(not bbox diagonals -- see modules/relational_loss.py\'s geodesic-'
                             'variant docstring for the SHIC-inspired design and why a naive '
                             'Euclidean->geodesic swap would silently kill the gradient). '
                             'Mutually exclusive with --bbox_norm/--live_mu_3d.')
    parser.add_argument('--geo_table_3d_path', type=str,
                        default='./experiments/guitar/geodesic_tables/guitar_geo_table_3d.pth',
                        help='--geodesic only: vertex-to-vertex geodesic table from '
                             'analysis/build_geodesic_tables.py')
    parser.add_argument('--geo_diag_3d', type=float, default=None,
                        help='override the 3D geodesic diameter used to normalize d_3D (default: the 3D '
                             "table's stored whole-mesh diagonal). For a photo showing only part of the object, "
                             'pass the visible-part diameter from analysis/estimate_visible_geo_diameter.py.')
    parser.add_argument('--geo_diag_2d', type=float, default=None,
                        help='override the 2D geodesic diameter used to normalize d_2D, instead of '
                             "taking the table's own stored `diagonal`. That stored value is a max "
                             'over the sampled CENTER rows only, so it underestimates the true '
                             'all-pairs diameter; the 3D side is a true all-pairs max, so the two '
                             'sides are not computed the same way. Measure the true value with '
                             'analysis/measure_2d_geodesic_diameter.py (1175.75 px for '
                             'segment_masks_pixel270_370, vs 1171.65 stored -- 0.35% low). '
                             'Added 2026-09-08 at Tal\'s request.')
    parser.add_argument('--geo_table_2d_path', type=str, default=None,
                        help='--geodesic and/or --cyc_weight>0: defaults to '
                             './experiments/guitar/geodesic_tables/<mask_basename>_geo_table_2d_seed<seed>.pth')
    parser.add_argument('--distance_weight', type=str, default=None, choices=['far', 'near'],
                        help='Reweight each sampled pair\'s Huber residual by its own '
                             'norm_d_2D before averaging, instead of every pair counting '
                             'equally (off by default). \'far\': pairs distant in the image '
                             'get more say in the loss. \'near\': the opposite (weight '
                             '1/norm_d_2D, floored). Composes with any normalization mode '
                             'above -- orthogonal concern, applied after normalization.')
    # MU-LEARNED (2026-09-14, Tal) -- see PROJECT_NOTES.md. `fixed` keeps every earlier run
    # bit-identical; `optimal` and `learned` make the zoom a fitted quantity instead of a guess.
    parser.add_argument('--mu_mode', type=str, default='fixed',
                        choices=['fixed', 'optimal', 'learned'],
                        help="how mu_3d_scale is set. 'fixed': the --mu_3d_scale constant "
                             "(default, unchanged behaviour). 'optimal': refit in CLOSED FORM "
                             "every step (s* = sum(b^2)/sum(a*b) over the sampled pairs, detached; "
                             "no parameter and no lr to tune). 'learned': an nn.Parameter trained "
                             'by Adam at --mu_lr, init 1.0. Geodesic loss only.')
    parser.add_argument('--mu_scope', type=str, default='global', choices=['global', 'segment', 'segment_aniso', 'grid_aniso', 'global_aniso', 'segment_aniso_xglobal', 'global_then_segment_aniso', 'dual_global_local_aniso', 'dual_global_segment_aniso'],
                        help='--mu_mode optimal/learned: one scale for the whole object, or one '
                             'PER FINE SEGMENT. A pair belongs to its CENTRE pixel\'s segment. '
                             'Per-segment is the anisotropy test: a single scalar can only fix a '
                             'uniform zoom, and the 09-10 measurement says mu<1 compresses the '
                             'NECK specifically, i.e. the distortion is regional.')
    parser.add_argument('--mu_switch_step', type=int, default=None,
                        help='--mu_scope global_then_segment_aniso: first step of stage B (per-segment ellipses, in-segment pairs)')
    parser.add_argument('--switch_nin', type=int, default=16, help='stage-B in-segment neighbours')
    parser.add_argument('--dual_local_nin', type=int, default=0,
                        help='--mu_scope dual_global_local_aniso: in-segment neighbours of the LOCAL (per-segment ellipse) term; '
                             'the GLOBAL term uses --num_neighbors_in/out_segment (Tal 2026-10-01)')
    parser.add_argument('--switch_hybrid', action='store_true',
                        help='global_then_segment_aniso: stage B is the HYBRID (in-seg pair -> its segment ellipse, cross-seg pair -> the global row); use with --switch_nout > 0 (Tal 2026-09-28)')
    parser.add_argument('--mu_aniso_fixed_path', type=str, default=None,
                        help='hand-made ellipses (Tal 2026-09-28), FROZEN: global_then_segment_aniso -> stage-B segment rows at the switch; segment_aniso_xglobal -> all rows (segments + global) from step 0')
    parser.add_argument('--switch_nout', type=int, default=0, help='stage-B out-of-segment neighbours')
    parser.add_argument('--mu_fix_seg_circle', nargs='+', default=None, metavar='SEG:VALUE',
                        help='global_then_segment_aniso: at the switch, fix these segments to a circle of that mu and freeze them; other rows keep learning (Tal 2026-09-29)')
    parser.add_argument('--stageA_fixed_circle', type=float, default=None,
                        help='global_then_segment_aniso: stage-A global ellipse frozen to a circle of this mu; stage-B per-seg rows start from it and learn (Tal 2026-09-29)')
    parser.add_argument('--stageA_fixed', action='store_true',
                        help='global_then_segment_aniso + --switch_hybrid: the --mu_aniso_fixed_path file (segments + global row) is loaded and FROZEN from step 0, so stage A uses the manual global row (Tal 2026-09-29)')
    parser.add_argument('--mu_grid', type=int, default=6,
                        help='--mu_scope grid_aniso: the ellipse field is a mu_grid x mu_grid lattice of nodes '
                             'over the mask bbox, bilinearly interpolated at each centre (2026-09-21)')
    parser.add_argument('--mu_fit_space', type=str, default='abs', choices=['abs', 'log'],
                        help="--mu_mode optimal: 'abs' (default) fits the scale on the ABSOLUTE "
                             'residual, which is what the loss itself measures -- a pair contributes '
                             'in proportion to its length squared, so long pairs dominate. '
                             "'log' fits on the RELATIVE residual instead (minimise "
                             '(log(d_3D/s) - log(d_2D))^2), where a 10%% error counts the same at '
                             'any length. Left OFF by default 2026-09-14: Tal wants the long '
                             'in-segment pairs to carry the scale, and unlike the in-segment / '
                             'geometric-mean fixes this one is a modelling choice, not a bug.')
    parser.add_argument('--mu_init_path', type=str, default=None,
                        help="--mu_mode learned only: .pth with 'mu_scale' [n_groups] to initialise the per-group "
                             'scales (analysis/perseg_mu_from_zs.py). Combine with --mu_lr 0 to keep them fixed.')
    parser.add_argument('--lora_w_rank', type=int, default=0,
                        help='LORA-W (2026-09-17): >0 freezes the phase-1 encoder and trains only a rank-r '
                             'update on --lora_w_layers (modules/lora.py). Checkpoints store the MERGED weights '
                             '(W + BA) under encoder_state_dict plus the raw update under lora_state. 0 = off.')
    parser.add_argument('--lora_w_layers', choices=['last', 'all'], default='last',
                        help='LORA-W: wrap only the output Linear (feature change has rank <= r) or all Linears.')
    parser.add_argument('--lora_w_train_alpha', type=float, default=1.0,
                        help='LORA-W: alpha of W + alpha * BA during TRAINING (2026-11-18, Tal: train at the alpha the matching '
                             'reads at). lora_state keeps the raw A, B, so export_pred_f_lora_alpha.py --alphas <this> reads it as trained.')
    parser.add_argument('--lora_w_l2', type=float, default=0.0,
                        help='LORA-W: weight of sum_layers ||alpha * BA||_F^2 in the loss (2026-11-18, Tal: shrink toward phase-1 in '
                             'training instead of reading at alpha 0.5). 0 = off.')
    parser.add_argument('--lora_w_lr', type=float, default=1e-3,
                        help='LORA-W: Adam lr for the LoRA parameters (replaces --lr for the encoder).')
    parser.add_argument('--mu_lr', type=float, default=1e-2,
                        help='--mu_mode learned: lr for the scale parameter only (its own Adam '
                             'param group). Much larger than the encoder lr on purpose -- it is '
                             'one number and it has 300 steps to arrive.')
    # rkd_spatial_angle3 (2026-09-15, Tal; old flags --spatial_angle_* still accepted) -- see rkd_spatial_angle3_loss().
    parser.add_argument('--rkd_spatial_angle3_weight', '--spatial_angle_weight', type=float, default=0.0,
                        help='weight of RKD\'s angle term in the SPATIAL domain: the angle at each '
                             'centre between rays to two neighbours, image pixels vs soft-mapped 3D '
                             'points. EUCLIDEAN angles on both sides. 0.0 (default) = off, bit-identical.')
    parser.add_argument('--rkd_spatial_angle3_min_ray_px', '--spatial_angle_min_ray_px', type=float, default=14.0,
                        help='drop triplets with an image-side ray shorter than this (default 14 = one '
                             'DINO patch; shorter rays give noise angles).')
    parser.add_argument('--rkd_spatial_angle3_balance', '--spatial_angle_balance', action='store_true',
                        help='diagnostic: print the relational and spatial-angle gradient norms and the '
                             'weight at equal / 1/3 / 1/10 of relational, then stop before backward. '
                             'Pair with --anchor_balance_from <checkpoint> to measure on a drifted state.')
    parser.add_argument('--mu_3d_scale', type=float, default=1.0,
                        help='Divide norm_d_3D by this AFTER normalization (1.0, the default, '
                             'is a no-op -- byte-identical to not passing this flag). '
                             'Mathematically identical to scaling mu_3D_reference/mu_3D_live by '
                             'the same value -- kept as a separate explicit knob so --bbox_norm\'s '
                             'reference stays a literal, honest bounding-box diagonal. A value > '
                             '1 raises the effective 3D-distance target the model has to satisfy, '
                             'pushing mapped points further apart in 3D for the same normalized '
                             'residual -- Tal\'s 2026-08-12 hypothesis for counteracting excessive '
                             'convergence (the headstock-drift family of problems). Composes with '
                             '--distance_weight and any normalization mode above.')
    parser.add_argument('--rkd_spatial_dist_weight', '--relational_weight', type=float, default=1.0,
                        help='Weight for the base relational term: loss = relational_weight * '
                             'relational_loss(...) + cyc_weight * cycle_consistency_loss(...) + '
                             'balance_weight * vertex_balance_loss(...). 1.0, the default, is a '
                             'no-op -- byte-identical to not passing this flag. Exists so '
                             '--relational_weight/--cyc_weight/--balance_weight can be swept '
                             'independently (alpha/beta/gamma) instead of the auxiliary terms '
                             'being the only tunable side of the combination.')
    parser.add_argument('--balance_weight', type=float, default=0.0,
                        help='Weight (beta) for an auxiliary vertex-usage load-balancing term: '
                             'loss = relational_weight * relational_loss(...) + balance_weight * '
                             'vertex_balance_loss(...) (+ cyc_weight * cycle_consistency_loss(...) '
                             'if that is also on). Off by default: 0.0 is an exact no-op. '
                             'Tal\'s 2026-08-15 request, after cycle_consistency_loss (both '
                             'variants) was parked without fixing the collapse problem: "start '
                             'from the simplest approach that could yield results." Adapted from '
                             'the Switch Transformer\'s additive MoE load-balancing auxiliary loss '
                             '(arXiv 2101.03961) -- a completely different, independent mechanism '
                             'from cyc_loss\'s reciprocity check, chosen because it is purely '
                             'additive (changes nothing about soft_map_to_vertices or any '
                             'existing loss, so it can be swept and abandoned exactly as cheaply '
                             'as cyc_weight was) rather than SwAV\'s stricter but much more '
                             'invasive Sinkhorn-Knopp equipartition, which would mean rewriting '
                             'the shared assignment mechanism itself. See '
                             'modules/vertex_balance_loss.py for the full design and the exact '
                             'formula as checked against the paper. '
                             'PARKED as of 2026-08-15, Tal\'s call: leave this at 0.0. Swept at '
                             '1e-4/3e-4/1e-3 (with --geodesic --mu_3d_scale 1) -- all increased '
                             'vertex coverage over baseline while keeping drift healthy (unlike '
                             'cyc_weight), but Tal\'s visual review found correspondence quality '
                             'WORSE despite the wider spread -- more vertices used, not more '
                             'correctly. See modules/vertex_balance_loss.py\'s CONCLUSION note.')
    parser.add_argument('--flip_features_path', type=str, default=None,
                        help='pixel features of the image flipped left-right (same extractor), for --flip_weight')
    parser.add_argument('--flip_weight', type=float, default=0.0,
                        help='flip consistency (2026-11-17): pixel (r, W-1-c) of the flipped image should map to the mirror of pixel '
                             '(r, c); 0 = off (byte-identical runs)')
    parser.add_argument('--cyc_weight', type=float, default=0.0,
                        help='Weight for a cycle-consistency term: loss = relational_loss(...) + '
                             'cyc_weight * cycle_consistency_loss(...) -- same additive lambda-'
                             'weighted pattern train_mapping_loss.py uses for lambda_map/'
                             'lambda_repel. Off by default: 0.0 is an exact no-op. Motivated by '
                             'Tal\'s 2026-08-14 measurement (only 603/4036 vertices, 14.9%%, '
                             'receive any pixel mapping at all; top 1%% of covered vertices '
                             'absorb 10.4%% of all pixels) -- penalizes many pixels collapsing '
                             'onto the same vertex via a differentiable reciprocity check '
                             '(soft-to-hard forward pick, then a geodesic-distance-weighted '
                             'expected round trip back), restricted to this run\'s fixed centers '
                             'for both legs -- see modules/cycle_consistency_loss.py for the '
                             'full design (styled after both modules/best_segmentation_buddies.py'
                             '\'s find_bsb and SHIC\'s L_cyc, arXiv 2407.18907, with geodesic '
                             'distance substituted for Euclidean). Requires a 2D geodesic table '
                             '(analysis/build_geodesic_tables.py, see --geo_table_2d_path) even '
                             'when --geodesic itself is off. Its round-trip distance is '
                             'normalized by the same geodesic diameter rkd_spatial_dist_loss '
                             'uses (see train()\'s own cyc_geo_diag_2d division and '
                             'modules/cycle_consistency_loss.py\'s docstring) so it lands in '
                             'roughly the same [0,~1] range as relational_loss -- start a sweep '
                             'at 1.0 (equal footing with --relational_weight\'s own default 1.0) '
                             'before trying more SHIC-style unequal weights, and watch '
                             'mu_3D_live/renders, not just vertex coverage, since this loss only '
                             'checks reciprocity, not geometric correctness. '
                             'PARKED as of 2026-08-15, Tal\'s call: leave this at 0.0 -- neither '
                             'this (hard-snap) nor --cyc_soft (fully-soft) ever beat the no-cyc '
                             'baseline on both drift and correspondence quality, and the root '
                             'cause traced back to this project having no SHIC-style absolute '
                             'per-pixel-to-vertex anchor at all, not to either implementation\'s '
                             'mechanics -- see modules/cycle_consistency_loss.py\'s CONCLUSION '
                             'note and PROJECT_NOTES.md (2026-08-15) before resuming this sweep.')
    parser.add_argument('--cyc_soft', action='store_true',
                        help='Use the fully-soft, SHIC-faithful cycle-consistency loss '
                             '(modules/cycle_consistency_loss_soft.py) instead of the default '
                             'hard-snap version (modules/cycle_consistency_loss.py). Checked '
                             'directly against SHIC (arXiv 2407.18907): the hard-snap version '
                             'collapses the forward pixel->vertex leg to a single argmin index '
                             'under no_grad, which SHIC never does (its p(xk|u)/p(v|xk) stay '
                             'full softmax distributions throughout L_cyc) -- and this project\'s '
                             'own 2026-08-14/15 training logs show the hard-snap forward leg '
                             'colliding constantly (refs=196-334/4036 out of 2048 centers), which '
                             'makes colliding pixels computationally indistinguishable to the '
                             'loss (identical vf_xk row -> identical gradient), a plausible reason '
                             'that sweep never produced a clean win. Only takes effect when '
                             '--cyc_weight > 0. See modules/cycle_consistency_loss_soft.py for '
                             'the full design. TESTED 2026-08-15 at cyc_weight 0.01/0.3 and found '
                             'WORSE than the hard-snap version on both coverage and drift, not '
                             'better -- the hard-snap bug was real but wasn\'t what stood between '
                             'this loss and being useful; see that module\'s CONCLUSION note. '
                             '--cyc_weight is parked at 0.0 as of this finding.')

    # Optimization -- same discipline as train_mapping_loss.py.
    parser.add_argument('--out_neighbors_segmented_only', action='store_true',
                        help='out-of-segment neighbours are never drawn from mask pixels that have no fine segment '
                             '(Tal, 2026-10-06). Off = every run before that date')
    parser.add_argument('--geodesic_domain_mask_path', type=str, default=None,
                        help='amodal mask the 2D geodesic table was built through (build_geodesic_tables.py flag of '
                             'the same name; Tal, 2026-10-07). Unset = every run before that date.')
    parser.add_argument('--drop_pixels_mask_path', type=str, default=None,
                        help='[H, W] bool, True = never a center, a neighbour or a cycle return pixel; the sampled centers and '
                             'the table stay the same, only the dropped ones are removed (Tal, 2026-11-24: the lifted table\'s '
                             'pixels with no surface point, build_lifted_geodesic_table.py <out>_miss.pth). Needs --geodesic.')
    parser.add_argument('--save_stageA_end', action='store_true',
                        help='write the end-of-stage-A save (encoder_checkpoint_stageA_end.pth, mu_aniso_stageA_end.pth) '
                             'even with --no_step_checkpoints (Tal, 2026-10-07: keep the stage-1 state, drop the 12 step dumps)')
    parser.add_argument('--no_step_checkpoints', action='store_true',
                        help='skip the intermediate encoder_checkpoint_step<N>.pth dumps, writing '
                             'only the final encoder_checkpoint.pth (2026-09-20). The step ladder '
                             'exists for the step-progression figure during method development; a '
                             'production sweep (e.g. the 132-instance DensePose-LVIS eval) never '
                             'reads it and pays 13 x 144MB = 1.9GB of writes per instance for it. '
                             'Affects only what is written to disk, never what is trained.')
    parser.add_argument('--num_iters', type=int, default=300)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--adam_eps', type=float, default=1e-12,
                        help="far below torch's 1e-8 default -- see "
                             'train_mapping_loss.py\'s identical flag for why')
    parser.add_argument('--checkpoint_every', type=int, default=25)
    parser.add_argument('--stop_at_drift', type=float, default=None,
                        help='stop early if mean cosine vs phase-1 features drops below '
                             'this (e.g. 0.9). Off by default.')

    parser.add_argument('--seed', type=int, default=0,
                        help='must match the phase-1 seed -- it is what restores the '
                             'Fourier basis (see load_phase1_encoder)')
    parser.add_argument('--train_seed', type=int, default=0,
                        help='seeds the TRAINING-time RNG: the per-step neighbour resampling in '
                             'sample_in_segment_neighbors/sample_out_segment_neighbors, which was '
                             'unseeded until 2026-08-29 and is a real source of run-to-run spread '
                             '(SEPARATE from --seed, which must keep matching phase-1). Change '
                             'this, not --seed, to repeat a recipe and measure its noise floor.')
    parser.add_argument('--out_dir', type=str,
                        default='./experiments/guitar/encoder_dino_relational')
    args = parser.parse_args()
    if args.mu_scope == 'dual_global_segment_aniso':   # old name (2026-10-01, renamed the same day; the first horse run's run_config has it)
        args.mu_scope = 'dual_global_local_aniso'

    if args.xseg_feat_mode != 'off' or args.xseg_feat_balance:
        # the split relies on the neighbour axis being cat([in, out]) and on ONE neighbour set for the whole
        # run: no stage switch, no dual set, no fixed neighbours, no resampled centers
        if args.xseg_feat_balance and args.xseg_feat_mode == 'off':
            raise SystemExit('--xseg_feat_balance needs --xseg_feat_mode (any mode; all three are measured)')
        if not args.geodesic:
            raise SystemExit('--xseg_feat_mode is only wired into the --geodesic branch')
        if args.mu_scope != 'segment_aniso' or args.mu_mode != 'learned':
            raise SystemExit('--xseg_feat_mode needs --mu_mode learned --mu_scope segment_aniso (in-segment pairs use '
                             'their segment ellipse; cross-segment pairs have no mu)')
        if args.num_neighbors_out_segment <= 0 or args.num_neighbors_in_segment <= 0:
            raise SystemExit('--xseg_feat_mode needs both --num_neighbors_in_segment and --num_neighbors_out_segment > 0')
        if args.fixed_neighbors or args.resample_centers:
            raise SystemExit('--xseg_feat_mode is not implemented with --fixed_neighbors / --resample_centers')
        if args.feat_student_mode != 'soft' or args.feat_detach_weights or args.feat_detach_features:
            raise SystemExit('--xseg_feat_mode sets its own student and detach; drop --feat_student_mode/--feat_detach_*')

    if args.mu_mode != 'fixed':
        if args.mu_3d_scale != 1.0:
            raise SystemExit('--mu_3d_scale is the FIXED constant; it cannot be combined with '
                             '--mu_mode %s, which fits the scale instead' % args.mu_mode)
        if args.dump_residuals:
            raise SystemExit('--dump_residuals and --mu_mode %s both take over the loss return '
                             'value; run the residual dump with --mu_mode fixed' % args.mu_mode)

    if args.init_encoder_checkpoint is None:
        args.init_encoder_checkpoint = os.path.join(args.init_encoder_dir,
                                                    'encoder_checkpoint.pth')
    train(args)
