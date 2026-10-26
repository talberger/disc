Our scripts that run INSIDE third-party clones (GPU machines only). Git source of truth = here;
on a new machine copy them into the clone: `cp external/sam3/*.py $DISC_WS/sam3_repo/` and
`cp external/pix2gestalt/*.py $DISC_WS/pix2gestalt_repo/`.
- sam3/        -> facebookresearch/sam3 clone at $DISC_WS/sam3_repo (env: env/requirements_sam3.txt)
- pix2gestalt/ -> pix2gestalt clone at $DISC_WS/pix2gestalt_repo (env: env/requirements_pix2gestalt.txt)
- pixal3d/     -> TencentARC/Pixal3D + microsoft/TRELLIS.2 on the Run:ai PVC (workspace pixal3d-env): install_runai.sh builds the env
