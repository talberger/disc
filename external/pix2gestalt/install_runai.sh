#!/bin/bash
# pix2gestalt env on Run:ai (Tal, 2026-10-28: content completion for occluded instances in the full run). Same as the pod's setup_env.sh,
# in the DISC image (tberger3/disc:v2: python 3.9 = what the pod venv used, torch 1.12.1+cu113), so it runs in the training workspace.
# Expects /workspace/pix2gestalt_repo/{stubs, pix2gestalt/{configs,ldm,inference.py,main.py}, pix2gestalt/ckpt/slim_ema.pt} fetched from
# the RunPod volume (s3get). Venv at /workspace/pix2gestalt_repo/venv = the path scripts/make_amodal_mask.sh / run_lvis_sam3_batch.sh use.
# Usage: bash external/pix2gestalt/install_runai.sh     (resumable)
set -eo pipefail
R=/workspace/pix2gestalt_repo; export PIP_CACHE_DIR=/workspace/.cache/pip
[ -f $R/pix2gestalt/ckpt/slim_ema.pt ] || { echo "no $R/pix2gestalt/ckpt/slim_ema.pt (fetch it first)"; exit 1; }
cp /workspace/disc/external/pix2gestalt/*.py $R/
[ -x $R/venv/bin/python ] || /usr/local/bin/python -m venv $R/venv
source $R/venv/bin/activate
pip install -q --upgrade pip wheel
pip install -q torch==1.12.1+cu113 torchvision==0.13.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
pip install -q "numpy<2" Pillow==9.5.0 opencv-python-headless==4.8.1.78 pytorch-lightning==1.4.2 omegaconf==2.1.1 einops==0.3.0 \
  transformers==4.22.2 kornia==0.6 torchmetrics==0.6.0 diffusers==0.12.1 fire==0.4.0 segment-anything==1.0 imageio==2.9.0 \
  albumentations==0.4.3 webdataset==0.2.5 test-tube ftfy regex tqdm scipy matplotlib "huggingface_hub<0.26" "setuptools<70"
cd $R/pix2gestalt
[ -d taming-transformers ] || git clone -q --depth 1 https://github.com/CompVis/taming-transformers.git
pip install -q -e taming-transformers/
[ -d CLIP ] || git clone -q --depth 1 https://github.com/openai/CLIP.git
pip install -q -e CLIP/ --no-deps
PYTHONPATH=../stubs:taming-transformers:CLIP python -c "
import torch; print('torch', torch.__version__, torch.cuda.is_available())
import sys; sys.path.insert(0, '.')
from ldm.models.diffusion.ddim import DDIMSampler
from ldm.util import instantiate_from_config
print('LDM IMPORT OK')"
echo "PIX2GESTALT INSTALL DONE"
