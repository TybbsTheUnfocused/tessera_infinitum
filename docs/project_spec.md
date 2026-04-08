# Project Specification: Perlin-Infinite

## 1. Project Overview
**Perlin-Infinite** is a generative art watchface for the Pebble smartwatch ecosystem. Inspired by the L-system and geometric artwork of Laurens Lapre, the watchface utilizes multi-octave Perlin noise to generate intricate, ephemeral digital art. 

To overcome the computational and memory constraints of the embedded ARM Cortex-M processors on Pebble hardware, the project utilizes an edge-compute hybrid architecture. A master canvas is generated server-side hourly, and the user's connected smartphone handles localized cropping, quantization, and Bluetooth transmission.

## 2. Core Mechanics & User Experience
* **Ephemeral Nature:** The artwork updates exactly once per hour.
* **Individual Uniqueness:** While all users share the same generated mathematical "universe" (the master canvas) for that hour, each user's watch displays a unique cropped perspective of that universe.
* **Persistence:** The watchface maintains the same visual state for the duration of the hour.
* **Hardware Agnostic:** The system dynamically adjusts the view and color space based on the connected watch platform (e.g., B&W for Aplite/Diorite, 64-color for Basalt/Time, round screens for Chalk).

## 3. System Architecture

The pipeline is divided into three distinct environments:

### 3.1 Backend (The Generator)
* **Environment:** Python script running via a scheduler (e.g., `systemd` timer or `cron`).
* **Task:** Generates a large-scale 2D matrix (e.g., 2048x2048) of continuous multi-octave Perlin or Simplex noise. 
* **Processing:** Maps the normalized noise values to a high-resolution color palette or vector field to simulate complex structural flows.
    * We will likely want to make several parameters for this canvas generation that define various artwork styles, color palettes, densities, etc. We can select from these style patterns randomly.
    * A significant part of the first step of this project will be creating and refining the generation script and logic so we can produce high quality artwork
    * We will then need to host the artwork somewhere - github pages, cloudflare, etc. 
* **Output:** Exports a standard image file (PNG/JPEG) and uploads it to a Content Delivery Network (CDN).
* **Cost Scaling:** Strictly $\mathcal{O}(1)$ compute per hour regardless of user base.

### 3.2 Middleware (PebbleKit JS - Edge Compute)
* **Environment:** JavaScript engine running on the user's iOS/Android device via the Pebble companion app.
* **Task 1 (Fetch):** Triggers on the hourly background tick. Fetches the current master canvas from the CDN.
* **Task 2 (Seed & Crop):** Uses a combination of the current hour (timestamp) and the unique `watchToken` to seed a deterministic random number generator. It selects a coordinate pair $(x, y)$ and crops a bounding box matching the connected watch's resolution (e.g., $144 \times 168$ or $180 \times 180$).
* **Task 3 (Quantization):** Applies a color reduction algorithm to map the high-res crop to the Pebble color space. 
    * *Basalt/Chalk:* Euclidean distance mapping to the 64-color Pebble palette.
    * *Aplite/Diorite:* Dithering algorithm (e.g., Atkinson or Floyd-Steinberg) to map to 1-bit monochrome.
* **Task 4 (Transmission):** Slices the resulting bitmap into dictionaries and transmits it to the watch via the `AppMessage` API.

### 3.3 Frontend (Pebble C App)
* **Environment:** C application compiled using the Rebble SDK.
* **Task:** Acts as a lightweight display terminal.
* **Memory Management:** Receives the byte array chunks from the phone, constructs the graphics bitmap in RAM, and invalidates the display layer to render the new artwork. Frees the previous hour's memory buffer to prevent heap fragmentation.

## 4. Extended Features (Phase 2)
* **Web Gallery:** As the backend generator creates the hourly master canvas, it will asynchronously push the file and its seed metadata to an object storage bucket (e.g., AWS S3, Cloudflare R2). A static frontend (e.g., built with React/Next.js) will query this bucket to allow users to view the historical archive of generated universes.

## 5. Development Milestones
1.  **Algorithmic Prototyping (Python):** Develop the noise generation and vector flow matrices to accurately mimic the desired aesthetic style.
2.  **API & Infrastructure:** Set up the backend cron job and CDN hosting for the master canvas.
3.  **Middleware Pipeline (JS):** Develop the PebbleKit JS logic for image fetching, deterministic coordinate selection, and color space quantization.
4.  **Embedded Client (C):** Write the Pebble C application to receive and draw the Bluetooth payload.
