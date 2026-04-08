# Design Specification: Perlin-Infinite Generator

**Date:** 2026-04-08
**Status:** Draft
**Topic:** Python Artwork Generation Engine

## 1. Objective
To create a robust, parameterized Python engine capable of generating high-resolution (2048x2048) procedural artwork. This artwork will serve as the "Universe" for the Perlin-Infinite Pebble watchface, providing an infinite variety of visual states while adhering to the hardware's 64-color palette constraints.

## 2. Architecture: The Unified Field
The system follows a "Unified Field" model where fluid Perlin/Simplex noise acts as a physics layer that distorts and colors rigid geometric fractal paths.

### 2.1 Component 1: Noise Core (The Universe)
*   **Engine:** NumPy-accelerated noise generation (using `vnoise` or `noise` library).
*   **Output:** A 2048x2048 matrix of normalized values [0.0, 1.0].
*   **Parameters:**
    *   `scale`: Zoom level of the noise.
    *   `octaves`: Detail complexity.
    *   `warping`: Boolean/Intensity for domain warping (noise-in-noise).
*   **Vector Mapping:** Every point $(x, y)$ in the noise matrix is mapped to an angle $[0, 2\pi]$, creating a global flow field.

### 2.2 Component 2: Fractal Path Generators
*   **Engines:** 
    *   **L-System Parser:** For recursive structures (Dragon curve, Koch snowflake, Peano-Gosper).
    *   **Space-Filling Logic:** For Hilbert and Peano curves.
*   **Interaction (Stiffness):**
    *   Each fractal vertex $P_i$ is offset by the local noise vector.
    *   Formula: $P'_i = P_i + (N(P_i) \cdot \text{VectorDirection} \cdot \text{Stiffness})$.
    *   High Stiffness = Liquid/Warped; Low Stiffness = Rigid/Geometric.

### 2.3 Component 3: Color & Palette Management
*   **Target Palette:** Pebble 64-color (6-bit RGB).
    *   **Logic:** Every channel (R, G, B) MUST be one of four values: `0x00`, `0x55`, `0xAA`, `0xFF`.
*   **Background:** Constant White (#FFFFFF) or Cream (#FFFFCC/Pebble equivalent).
*   **Mapping Strategies:**
    *   **Noise-to-Color:** Indexing a gradient based on local noise value.
    *   **Path-to-Color:** Gradient progression from start-to-finish of the fractal curve.
    *   **Angle-to-Color:** Hue determined by the direction of the local flow vector using a standard 360-degree color wheel mapping.
*   **Sub-Palettes:** Random selection of 2–16 high-contrast colors (e.g., "Deep Sea" blue-greens, "Solar" red-yellows) to ensure readability against white.
*   **Implementation Mandate:** All color mapping and quantization MUST be performed using NumPy-based vectorization to avoid per-pixel Python loops and meet the <10s generation target.

### 2.5 Component 5: Data Structures
*   **Vector Field:** The Angle matrix (0 to 2π) MUST be maintained as a standalone NumPy array for complex 'stiffness' behaviors.

### 2.4 Component 4: Export & Persistence
*   **Master Image:** 2048x2048 PNG.
*   **Metadata:** JSON file containing:
    *   `seed`: Deterministic random seed.
    *   `parameters`: Dictionary of style values (stiffness, scale, palette used).
    *   `bounds`: Active area of the artwork.
*   **Package Management:** `uv` for dependency and venv management.

## 3. Data Flow
1.  **Seed Initialization:** Generate unique seed for the hour.
2.  **Noise Generation:** Create the 2D flow field.
3.  **Path Generation:** Compute fractal coordinates.
4.  **Distortion Pass:** Apply stiffness/offset based on noise.
5.  **Rasterization:** Draw the path to a 2048x2048 canvas using Pillow.
6.  **Quantization:** Ensure output strictly uses the Pebble 64-color palette.
7.  **Export:** Save PNG + JSON for CDN upload.

## 4. Success Criteria
*   Visual variety that feels distinct hour-to-hour.
*   Strict adherence to Pebble color space.
*   Performance: Full 2048x2048 generation < 10 seconds on modern CPU.
