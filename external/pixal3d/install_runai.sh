#!/bin/bash
# Pixal3D (TencentARC, TRELLIS.2 backbone) env on the Run:ai PVC (Tal, 2026-10-26). Run INSIDE the `pixal3d-env` workspace
# (image pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel: torch 2.6.0+cu124, nvcc 12.4). Everything persistent lives on /workspace:
#   venv  /workspace/envs/pixal3d  (--system-site-packages: reuses the image's torch; valid while the workspace keeps this image)
#   repos /workspace/pixal3d_repo, /workspace/trellis2_repo;  HF cache /workspace/.cache/huggingface
# Steps follow TRELLIS.2 setup.sh (--basic --flash-attn --nvdiffrast --nvdiffrec --cumesh --o-voxel --flexgemm, no --new-env)
# + Pixal3D README (requirements.txt, natten 0.21.0, utils3d wheel). Skipped: pillow-simd + `sudo apt` (Pixal3D pins pillow 12).
# Resumable: each step leaves /workspace/envs/pixal3d/.done_<step>. Log: run it as
#   setsid nohup bash external/pixal3d/install_runai.sh > /workspace/logs/pixal3d_install.log 2>&1 < /dev/null &
set -euo pipefail
WS=/workspace; V=$WS/envs/pixal3d; X=$WS/envs/pixal3d_ext
export HF_HOME=$WS/.cache/huggingface MAX_JOBS=${MAX_JOBS:-8}
ARCH=$(python -c "import torch; c=torch.cuda.get_device_capability(); print(f'{c[0]}.{c[1]}')")   # e.g. 8.6 (A5000 / A6000)
export TORCH_CUDA_ARCH_LIST=$ARCH
echo "##### GPU arch $ARCH, python $(python --version) [$(date -u +%T)]"
[ -x $V/bin/python ] || python -m venv --system-site-packages $V
source $V/bin/activate
mkdir -p $X
run() { local n=$1; shift; [ -f $V/.done_$n ] && { echo "== $n: done before"; return 0; }; echo "##### $n [$(date -u +%T)]"; ( "$@" ); touch $V/.done_$n; echo "== $n ok [$(date -u +%T)]"; }

[ -d $WS/trellis2_repo ] || git clone --recursive https://github.com/microsoft/TRELLIS.2.git $WS/trellis2_repo
[ -d $WS/pixal3d_repo ] || git clone https://github.com/TencentARC/Pixal3D.git $WS/pixal3d_repo

run basic bash -c "pip install imageio imageio-ffmpeg tqdm easydict opencv-python-headless ninja trimesh transformers tensorboard pandas lpips zstandard kornia timm \
  && pip install git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8"
# flash-attn: a prebuilt wheel if one matches, else a long source build; if it fails, run Pixal3D with ATTN_BACKEND=sdpa (README tip)
run flash_attn bash -c "pip install flash-attn==2.7.3 --no-build-isolation" || echo "!! flash-attn FAILED -> use ATTN_BACKEND=sdpa"
run nvdiffrast bash -c "rm -rf $X/nvdiffrast && git clone -b v0.4.0 https://github.com/NVlabs/nvdiffrast.git $X/nvdiffrast && pip install $X/nvdiffrast --no-build-isolation"
run nvdiffrec bash -c "rm -rf $X/nvdiffrec && git clone -b renderutils https://github.com/JeffreyXiang/nvdiffrec.git $X/nvdiffrec && pip install $X/nvdiffrec --no-build-isolation"
run cumesh bash -c "rm -rf $X/CuMesh && git clone --recursive https://github.com/JeffreyXiang/CuMesh.git $X/CuMesh && pip install $X/CuMesh --no-build-isolation"
run flexgemm bash -c "rm -rf $X/FlexGEMM && git clone --recursive https://github.com/JeffreyXiang/FlexGEMM.git $X/FlexGEMM && pip install $X/FlexGEMM --no-build-isolation"
run o_voxel bash -c "rm -rf $X/o-voxel && cp -r $WS/trellis2_repo/o-voxel $X/o-voxel && pip install $X/o-voxel --no-build-isolation"
run pixal_reqs bash -c "cd $WS/pixal3d_repo && pip install -r requirements.txt"
run natten bash -c "NATTEN_CUDA_ARCH=$ARCH NATTEN_N_WORKERS=$MAX_JOBS pip install natten==0.21.0 --no-build-isolation"
run utils3d_pixal bash -c "pip install https://github.com/LDYang694/Storages/releases/download/20260430/utils3d-0.0.2-py3-none-any.whl"
echo "##### import check [$(date -u +%T)]"
cd $WS/pixal3d_repo && python -c "
import importlib, torch
for m in ['flash_attn', 'nvdiffrast.torch', 'nvdiffrec_render', 'cumesh', 'flex_gemm', 'o_voxel', 'natten', 'utils3d', 'moge']:
    try: importlib.import_module(m); print('  ok  ', m)
    except Exception as e: print('  FAIL', m, repr(e)[:150])
from pixal3d.pipelines import Pixal3DImageTo3DPipeline
print('IMPORTS OK', torch.__version__, torch.cuda.get_device_name())"
echo "PIXAL3D INSTALL DONE [$(date -u +%T)]"
