# Attribution and licenses

## EvoVid origin
This independent version is based on the supplied public EvoVid Pocket branch at commit `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`. The original MIT license is retained in `LICENSE`. `vision/upstream_vision.py` is a preserved copy of `desktop/evovid/vision.py`; its strict OpenCV-major-version gate is used directly. The new backend, interactive review workflow, approval-driven renderer, controls, traces, test fixtures, private AWS template and reports are separate competition-version work. The original upstream directory was not modified.

Existing EvoVid contributed the strict OpenCV 5 safeguard and design precedent of explainable heuristics. Do not describe the whole project as written from scratch for this contest. AI coding assistance was used.

## Dependencies
- OpenCV / opencv-python-headless: Apache-2.0 distribution with bundled dependency notices. Official project: https://pypi.org/project/opencv-python-headless/5.0.0.93/
- NumPy: BSD-3-Clause and bundled notices.
- FastAPI, Starlette, Pydantic, Uvicorn, HTTPX, pytest and related Python packages retain their upstream licenses. Exact installed distributions are listed in `requirements.lock`; their `.dist-info` license metadata is present after installation.
- FFmpeg licensing depends on its build and enabled components. The tested system build is 7.1.5; bundled imageio-ffmpeg 0.6.0 uses Linux FFmpeg 7.0.2-static. libx264 introduces GPL obligations for distributed binaries. This source package does not include a copied FFmpeg executable or virtual environment; the first-run installer obtains the official imageio-ffmpeg distribution from PyPI. If distributing a ready-made image/binary, review and satisfy all applicable FFmpeg/x264 source-offer/license obligations. https://ffmpeg.org/legal.html
- `imageio-ffmpeg` is obtained from its official PyPI distribution: https://pypi.org/project/imageio-ffmpeg/0.6.0/
- Optional DOM QA uses official npm `jsdom` under its upstream MIT license; it is not a runtime dependency and is not bundled.

## Media and fonts
All five `examples/synthetic-*.mp4` source clips were generated from authored geometric shapes and OpenCV's built-in text drawing; their tone is a generated sine wave. No human likenesses, model weights, copyrighted music or downloaded footage are included. They are synthetic tests under the project MIT license, not recordings of real user work. The all-black fixture contains deliberately black pixels; filename, manifest and report identify it as synthetic. The UI uses installed system fonts and no externally hosted assets.

User uploads are not included in the distribution. The runtime and QA-generated intermediate directories are excluded from source packaging.

## Bundled sample rights

Authored bundled sample captions, geometric artwork and synthetic fixture compositions are covered by the project MIT license. Referenced film/artist/product names do not convey trademark rights or rights to third-party media. Font binaries, stock footage, music recordings, model weights and real provider response datasets are not bundled.
