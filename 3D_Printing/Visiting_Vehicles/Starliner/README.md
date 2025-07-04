# Attribution

This thing was created by Thingiverse user astro_sam, and is licensed under cc.
CST-100 Starliner and Atlas V N22 by astro_sam on Thingiverse: https://www.thingiverse.com/thing:4060978

This was modified by Digisembler for ISS MIMIC use.

# Slicer Recommendation 

# CST100 Starliner-ISS Mimic Print Profile

![image](https://github.com/user-attachments/assets/a317cf4b-40ec-4e3e-89c7-850ebb066efc)

Recommend a white PLA. The crew module is a grayish color, and the service module is white. Best to print upside down so the aft end of the vehicle looks good. 

Most settings are default, really just need tree supports on build plate only. 

This profile was made in **Bambu Studio** / **H2D** with a **0.4 mm nozzle** and **Overture PLA**.  
The goal is a crisp 0.12 mm-layer display print that’s still sturdy enough to survive handling.

| Category | Setting | Value |
|----------|---------|-------|
| **Layer Height** | Layer height | **0.12 mm** |
|  | Initial layer height | 0.20 mm |
| **Line Widths** | Default / Outer | 0.42 mm |
|  | Inner wall | 0.45 mm |
|  | Initial layer | 0.50 mm |
|  | Top surface | 0.42 mm |
|  | Sparse infill | 0.45 mm |
|  | Internal solid infill | 0.42 mm |
| **Walls & Shells** | Wall loops | 4 |
|  | Top surface pattern | Monotonic |
|  | Top shell layers | 9 (≈ 0.8 mm) |
|  | Bottom surface pattern | Monotonic |
|  | Bottom shell layers | 7 |
|  | Bottom shell thickness | 0 mm *(auto from layers)* |
|  | Internal solid infill pattern | Rectilinear |
| **Sparse Infill** | Density | 15 % |
|  | Pattern | Gyroid |
|  | Anchor length | 400 % |
|  | Anchor max length | 20 mm |
| **Seam** | Position | Aligned |
|  | Smart scarf seam | ✓ |
|  | Scarf angle threshold | 155 ° |
|  | Scarf steps | 10 |
| **Speed – Initial Layer** | Perimeter / Wall | 40 mm s⁻¹ |
|  | Infill | 70 mm s⁻¹ |
| **Speed – Other Layers** | Outer wall | 60 mm s⁻¹ |
|  | Inner wall | 120 mm s⁻¹ |
|  | Small perimeters | 50 % of inner-wall speed |
|  | Small perimeter threshold | 0 mm |
|  | Sparse infill | 100 mm s⁻¹ |
|  | Internal solid infill | 150 mm s⁻¹ |
|  | Vertical shell speed | 80 % |
|  | Top surface | 150 mm s⁻¹ |
|  | Slow down for overhangs | ✓ |
|  | Bridge | 50 mm s⁻¹ |
|  | Gap infill | 50 mm s⁻¹ |
|  | Support | 150 mm s⁻¹ |
|  | Support interface | 80 mm s⁻¹ |
| **Support** | Enabled | ✓ |
|  | Type | Tree (auto) |
|  | Style | Default |
|  | Threshold angle | 20 ° |
|  | On build plate only | ✓ |
|  | Support critical regions only | ✓ |
|  | Remove small overhangs | ✓ |
|  | Raft layers | 0 |

> **Tip:** These numbers are tuned for Overture PLA on an enclosed Bambu H2D.  
> If you swap material, nozzle size, or printer, retune temps, cooling, and speeds accordingly.
