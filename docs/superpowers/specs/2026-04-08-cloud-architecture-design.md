# Tessera ad Infinitum: Cloud Architecture & Deployment Design

**Date:** 2026-04-08
**Status:** Finalized (revised 2026-04-08 — pre-cropped slice strategy)

## 1. Objective
To design a serverless, scalable, and zero-egress-cost cloud architecture that enables "One Generation, Infinite Watchfaces." The system generates a master 2048×2048 canvas on an hourly cadence and serves pre-cropped, platform-sized slices to individual Pebble smartwatches, while also powering a historical web gallery.

## 2. Target Platforms
Color Pebble platforms only. B&W platforms (aplite, diorite) are out of scope — the Pebble 64 palette and fluid color gradients are core to the aesthetic.

| Platform | Device              | Resolution | Shape  |
|----------|---------------------|------------|--------|
| basalt   | Pebble Time / Steel | 144×168    | rect   |
| chalk    | Pebble Time Round   | 180×180    | round  |
| emery    | Pebble Time 2       | 200×228    | rect   |

## 3. Global Architecture

The pipeline uses the **"All-in-One Serverless Stack"** with **pre-computed slices**: the orchestrator does all the expensive work (render + crop + palette-encode) once per hour, and the edge Worker becomes a thin selector over pre-baked assets.

### 3.1 The Compute (GitHub Actions)
- **Role:** Orchestration engine — render, slice, encode, upload.
- **Trigger:** Hourly cron (`0 * * * *`).
- **SLA note:** GitHub scheduled workflows are best-effort; delays of 5–15+ minutes are common under load, and schedules are paused after 60 days of repo inactivity. Hourly cadence is acceptable under this SLA; anything tighter would need a CF Cron Trigger instead.
- **Execution (`scripts/orchestrator.py`):**
    1. Derives a deterministic seed from the current UTC hour (`seed = hash(YYYYMMDDHH)`).
    2. Selects curated aesthetic parameters via a seeded RNG so the run is fully reproducible from `(seed, generator git SHA)` alone.
    3. Invokes `Engine.generate_universe(seed, params)` to produce the 2048×2048 master PNG + metadata dict.
    4. Saves the master as an **indexed-color PNG** using the Pebble 64 palette (`PIL.Image.quantize()` with a custom palette image built from `PEBBLE_64_PALETTE`, preserving canonical index ordering). This shrinks R2 storage, eliminates antialiasing drift off the palette, and makes downstream palette lookups trivial.
    5. **Pre-slices** the canvas: for each color platform, generates **N = 100** crops at random `(x, y)` offsets (seeded from the master seed so the slice set is also reproducible). For `chalk`, applies a circular alpha mask so the round display's corners are transparent/ignored.
    6. For each slice, encodes the pixels as a **raw Pebble-64 byte array** — one byte per pixel, value = palette index 0..63. This is the exact format the watch writes to its display buffer.
    7. Uploads master, metadata, and all slices to R2 (see §3.2).
- **Authentication:** GitHub → Cloudflare via **OIDC federation** (no long-lived API tokens in GitHub secrets). The Action assumes a Cloudflare API token scoped to write-only on the R2 bucket prefix.

### 3.2 The Storage (Cloudflare R2)
- **Role:** Asset repository. Zero egress fees.
- **Structure:**
    ```
    latest/
      canvas.png                       # indexed-color master, 2048x2048
      metadata.json                    # generation contract (see §4)
      slices/
        basalt/{000..099}.bin          # raw Pebble-64 byte arrays, 144*168 bytes
        chalk/{000..099}.bin           # 180*180 bytes, round-masked
        emery/{000..099}.bin           # 200*228 bytes
        index.json                     # slice manifest (count, offsets, platform dims)
    archive/
      YYYY/MM/DD/HH-canvas.png         # master only — slices are NOT archived
      YYYY/MM/DD/HH-metadata.json
    ```
- **Rotation:** `latest/slices/*` is **overwritten in place** each hour. Only the current hour's slice set lives in R2 at any time (~10 MB total across all platforms). Historical canvases are archived as indexed PNGs for the gallery, but historical slices are not — if a past hour ever needs to be replayed for a client, the orchestrator can re-slice from the archived master (determinism guarantees the same result).

### 3.3 The Edge API (Cloudflare Worker)
- **Role:** Thin selector. No image processing at the edge.
- **Endpoint 1: `GET /api/slice`**
    - **Parameters:** `platform` (`basalt` | `chalk` | `emery`), `idx` (0..99, optional).
    - **Logic:**
        1. If `idx` is omitted, hash the request (e.g., `client_id + hour_bucket`) into `[0, 100)` to pick a deterministic slice for this client-hour. This keeps individual watches visually varied hour-to-hour while giving the edge cache a small, finite key space.
        2. Fetch `latest/slices/{platform}/{idx:03d}.bin` from R2.
        3. Return it with `Content-Type: application/octet-stream` and `Cache-Control: public, max-age=3600, immutable`. The Worker sets `Cache-Key` to `(hour_bucket, platform, idx)` so the CF edge caches at most **300 objects per POP per hour** (3 platforms × 100 slices). After the first hit in a region, every subsequent request is served from the edge for free.
- **Endpoint 2: `GET /api/gallery`**
    - Returns a paginated JSON list of historical master canvases from `archive/`. Consumed by the gallery frontend.
- **What the Worker does NOT do:** no Cloudflare Image Resizing, no PNG decoding, no palette quantization, no cropping. All of that happens once per hour in the orchestrator.

### 3.4 The Gallery Frontend (Cloudflare Pages)
- **Role:** Public showcase at `tesserainfinitum.com`.
- **Execution:** Static site (framework TBD) hosted on Cloudflare Pages, consumes `/api/gallery`, renders a lazy-loaded grid of every master ever generated.

### 3.5 The Client (Pebble Watchface + PebbleKit JS)
- **Role:** Endpoint viewer.
- **Logic:**
    1. On hourly tick, the Pebble C app asks PebbleKit JS for an update.
    2. PebbleKit JS calls `GET /api/slice?platform={this.platform}` (no `idx` — the Worker picks one deterministically per client per hour).
    3. PebbleKit JS receives `W*H` bytes of palette indices and streams them to the watch over BLE.
    4. The watch maps each index → Pebble-64 color and writes directly to the framebuffer. No decompression, no color math on-device.

## 4. Metadata Contract

`metadata.json` is a **public, versioned contract** consumed by the Worker, the gallery, and any future tooling. Fields may be **added freely**; renaming or removing existing fields is a breaking change and must bump `contract_version`.

```json
{
  "contract_version": 1,
  "generator_sha": "1e0fd67…",
  "generated_at_utc": "2026-04-08T14:00:00Z",
  "seed": 1743863400,
  "params": { "mode": "fractal_pure", "...": "..." },
  "final_whitespace": 0.21,
  "adaptive_passes": 7,
  "slice_manifest": {
    "count_per_platform": 100,
    "platforms": {
      "basalt": { "w": 144, "h": 168, "shape": "rect" },
      "chalk":  { "w": 180, "h": 180, "shape": "round" },
      "emery":  { "w": 200, "h": 228, "shape": "rect" }
    },
    "offsets": { "basalt": [[x0,y0], ...], "chalk": [...], "emery": [...] }
  }
}
```

The `offsets` array records the `(x, y)` top-left of each slice in the master so any slice can be re-derived from the archived canvas without re-running the orchestrator. Load-bearing keys for downstream consumers: `contract_version`, `generator_sha`, `seed`, `params`, `slice_manifest`.

## 5. Determinism & Replay

Every hour's output must be reproducible from `(generator_git_sha, seed, params)` alone. This is what makes "archive masters only, not slices" safe — if a client ever asks for a past hour's slice, the orchestrator can check out the archived `generator_sha`, re-run with the archived `seed` + `params`, and produce a byte-identical result.

Requirements this imposes on the generator repo:
- **Never change seed-derivation logic** (`np.random.seed(seed)` at the top of `generate_universe`, `seed + pass_idx*1000` for adaptive passes, `seed + idx*100` for segmented sub-regions) without bumping `contract_version`.
- **Never change the Pebble 64 palette ordering** — byte-array indices reference palette positions, not RGB values. Reordering the palette silently corrupts every archived slice set's color mapping.
- The orchestrator must record the generator git SHA into `metadata.json` at render time.

## 6. Trade-offs & Rationale

- **Why pre-crop instead of dynamic crop?** Dynamic cropping via a Cloudflare Worker means every request that misses the cache pays for a PNG fetch + decode + crop + palette-encode cycle on the edge. Pre-cropping does this work **once per hour** in the orchestrator (where compute is free under the GitHub Actions budget), leaving the Worker as a sub-millisecond file proxy. It also gives the CF edge cache a **bounded key space** (300 objects/hour globally), so cache hit rates approach 100% after the first request per POP.

- **Why 100 slices per platform?** Enough visual variety that no two watches in a friend group are likely to show the same crop, cheap enough in storage (~10 MB total per hour). If the number ever needs tuning, it's a single constant in the orchestrator and a field in `slice_manifest` — clients and Worker read it dynamically.

- **Why overwrite slices instead of archiving them?** Slices are a derivative artifact. The master canvas + metadata + deterministic generator is sufficient to regenerate any historical slice on demand, and the gallery only needs the master anyway. Archiving slices would waste ~240 MB/day for no new information.

- **Why indexed-color PNG for the master?** (1) It's the on-disk form of "already snapped to Pebble 64" — the orchestrator's slice step becomes a trivial array read, no re-quantization. (2) Roughly 4× smaller on disk than RGB PNG. (3) Eliminates any risk of antialiasing drift introducing off-palette colors between generator and Worker.

- **Why Cloudflare R2?** AWS S3 charges for egress. With thousands of watches pulling hourly, zero-egress pricing is the difference between sustainable and unsustainable.

- **Why byte-array transmission to the watch?** Pebbles have extremely limited RAM and BLE bandwidth. Shipping palette indices (1 byte/pixel) instead of PNG means the watch does zero decode work and BLE payloads are as small as physically possible for the display resolution.

- **Why OIDC instead of GitHub secrets?** No long-lived credentials in the repo. The token is minted per-run and scoped write-only to the R2 bucket prefix.

- **Why deterministic `idx` selection per client-hour?** Random `(x, y)` per-request would give near-zero cache hit rate (every watch requests a unique crop). Hashing `client_id + hour_bucket` into `[0, 100)` preserves per-watch visual variety while collapsing the global request space to exactly 300 cacheable objects/hour.
