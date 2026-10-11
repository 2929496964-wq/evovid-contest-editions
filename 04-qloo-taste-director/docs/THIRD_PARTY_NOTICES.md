# Third-party notices

## EvoVid upstream

Public source: https://github.com/2929496964-wq/evovid-pocket

Baseline: `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`.

MIT license retained in root `LICENSE`. The `vendor/evovid/` files are unmodified upstream reference copies. `taste/models.py`, `taste/store.py` and `taste/render.py` adapt its protocol/persistence/rendering concepts. This edition is a substantial independent local development branch; it does not claim all of EvoVid was newly created during the contest.

## Runtime dependencies

Packages are installed from official PyPI and pinned in `requirements.lock`. They are not relicensed by this project's MIT license. Consult the installed distributions' license metadata for the exact versions.

- FastAPI, Starlette, HTTPX, Pydantic, Uvicorn and related runtime packages retain their respective open-source licenses.
- Pillow retains its HPND/PIL license.
- imageio-ffmpeg retains its package license; its bundled FFmpeg executable has its own FFmpeg licensing and build configuration. A system encoder also retains its own license. Review the actual encoder distribution obligations before redistributing a packaged binary/container. No FFmpeg executable is copied into this source archive.
- Python and optional test tooling retain their own licenses.

No external fonts, copyrighted film/artist images, movie footage, sound recordings or model weights are bundled. System fonts are used at runtime. The demo geometric visual compositions are authored for this project. Film/artist titles are reference names, not endorsements or media-use licenses. The app does not download reference images even when a provider response contains them.

Qloo service access, data usage and retention remain subject to Qloo's terms and the entrant's authorized access; a source-code license does not grant service rights. No Qloo source package or dataset is redistributed here. DEMO data is synthetic and labeled.

## Bundled sample rights

Authored bundled sample captions, geometric artwork and synthetic fixture compositions are covered by the project MIT license. Referenced film/artist/product names do not convey trademark rights or rights to third-party media. Font binaries, stock footage, music recordings, model weights and real provider response datasets are not bundled.
