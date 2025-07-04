### Dream Chaser Model
This model was based on the amazing CAD model created by Matthew Weippert on [grabcad](https://grabcad.com/library/dream-chaser-tenacity-1) - modified to work with mimic. Shooting star module is our own creation, solar arrays based on the arrays from the CSA soyuz model.

# Slicer Recommendation 

# Dreamchaser-ISS Mimic Print Profile

![image](https://github.com/user-attachments/assets/44e39588-a531-4746-8b0c-cc3891bafd15)

![image](https://github.com/user-attachments/assets/8581b157-432a-46ea-b3c2-c9e03d363e56)

Recommend a white PLA for printing if you plan to paint it.

Most settings are default, really just need tree supports on build plate only. The nozzles break off easily. 

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
