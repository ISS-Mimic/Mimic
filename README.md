<!-- =========================================================
  ISS Mimic  •  Re-create the ISS attitude & telemetry in real-time
  ========================================================= -->

<p align="center">
  <img src="Pi/imgs/main/ISSmimicLogoPartsGroundtrack.png" width="420" alt="ISS Mimic logo">
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-blue.svg"></a>
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/ISS-Mimic/Mimic">
  <a href="https://discord.gg/zPKyE6hBSe"><img alt="Discord Chat" src="https://img.shields.io/discord/764217406041882684"></a>
  <a href="https://www.youtube.com/watch?v=W9iZBjzOEEQ"><img alt="Demo" src="https://img.shields.io/badge/▶ Demo%20Video-red?logo=youtube&logoColor=white"></a>
</p>

> **ISS Mimic** is an open-source mash-up of hardware + software that **mirrors the International Space Station’s solar-array and radiator motion** in real time.  
> 🍓 Runs on Raspberry Pi • 🛠 12 motors drive a 3-D-printed ISS • 📈 Live telemetry visualizer

---

ISS Mimic is a 3D printed model of the International Space Station that connects to the actual live data from the real ISS to control a model that rotates solar panels and radiators to match the real one in real time. The goal of this project is to connect people with the ISS. There are three different mimic models: Mimic, Mini Mimic, and Edu Mimic. These models are designed for teachers, students, museums, hobbyists, and anyone who wants to learn more about the ISS. 

Join the discussion, help out, ask for help, chat about the ISS here: [Mimic Discord](https://discord.gg/zPKyE6hBSe)

![PXL_20231210_003701830](https://github.com/user-attachments/assets/27b69560-8007-48d9-a087-6f27fd00f06d)

<details>
<summary>Table of Contents</summary>

- [Features](#features)
- [Quick Start (Raspberry Pi)](#quick-start-raspberry-pi)
- [Project Architecture](#project-architecture)
- [Build Your Own Model](#build-your-own-model)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)
</details>

---

### Features
- **Live telemetry pull** from NASA’s Lightstreamer endpoint – no scraping needed  
- **Interactive dashboards** (more capable than the original ISSLive site)  
- **Real-time kinematics**: 12-axis motion matches α- and β-gimbal joint angles  
- **Modular design**: Separate Pi (telemetry & UI) ↔ Arduino (motor control)  
- **Low- / High-fidelity STLs** you can print today  

### Quick Start (Raspberry Pi)
```bash
# 1. Clone & install deps
  git clone --depth 1 https://github.com/ISS-Mimic/Mimic.git/ 
  cd ~/Mimic
  python setup.py

# 2. Run the Mimic GUI dashboard
  cd ~/Mimic/Pi/
  python GUI.py
```
Full software guide: [Wiki » Software Setup Instructions](https://github.com/ISS-Mimic/Mimic/wiki/Build-Instruction%3A-Mimic-Software-Setup-Instructions).

### Project Architecture
```text
┌──────────┐              ┌──────────────┐                ┌──────────────┐                 ┌──────────┐
│ NASA LS  │────────────▶│ Raspberry Pi │───────────────▶│  Arduino(s)  │───────────────▶│  Motors  │
└──────────┘  telemetry   └──────────────┘  joint angles  └──────────────┘  motor commands └──────────┘
```
*Pi side* (Python + Kivy) shows telemetry dashboards and forwards joint targets.  
*Arduino side* (C++) drives stepper/servo motors in the 3-D-printed truss.

### Build Your Own Model
| Fidelity | STL pack | Status |
|----------|----------|--------|
| Low      | [`/3D_Printing`](3D_Printing) | ✔ Complete |
| High     | `/3D_Printing/high_fidelity` | 🚧 In progress – contributors welcome! |

Mechanical details, BOM, and wiring live in the **[Hardware Wiki section](https://github.com/ISS-Mimic/Mimic/wiki/Hardware)**.

### Screenshots
<p align="center">
  <img src="https://github.com/user-attachments/assets/071d90c0-504c-4c9c-95a2-5e7aa4a1db94" width="250" alt="Mimic1">
  <img src="https://github.com/user-attachments/assets/2579f6cb-1be1-4827-b076-0dc5c3374468" width="250" alt="Mimic2">
  <img src="https://github.com/user-attachments/assets/b616095f-93a2-427e-b801-ac2992f1a6f7" width="250" alt="Mimic3">
  <br>
  <img src="https://github.com/user-attachments/assets/737c447c-e9c7-4a40-9878-38ae68ba5e51" width="250" alt="Mimic4">
  <img src="https://github.com/user-attachments/assets/92358d93-7acd-4216-acdd-765e4efc8fc7" width="250" alt="Mimic5">
  <img src="https://github.com/user-attachments/assets/3afdb129-0f15-4075-b9af-4b07f93a4e77" width="250" alt="Mimic6">
  <br>
  <img src="https://github.com/user-attachments/assets/25cdaaa9-a04e-401b-a5d2-0039b911d47c" width="250" alt="Mimic7">
  <img src="https://github.com/user-attachments/assets/c21a9d0b-10a5-4251-90ff-319e66b724d0" width="250" alt="Mimic8">
  <img src="https://github.com/user-attachments/assets/5c7bd170-9f16-42e7-be29-4d884cc17b1a" width="250" alt="Mimic9">
</p>

### Contributing
We 💙 pull requests! Start by opening an issue or chatting on **[Discord](https://discord.gg/zPKyE6hBSe)**.  
Coding guidelines:
1. Follow **PEP 8** and keep GUI layout in **`.kv` files** (Kivy best practice).  
2. Fix all our mistakes. 

Other help:
-Feel free to suggest ideas! Best place to talk is out discord, or feel free to publish an issue

### Roadmap
- [ ] Finish high-fidelity CAD & release STEP source
- [ ] Complete build guide
- [ ] Finish Kivy telemetry screens  

### License
This project is licensed under the MIT License – see [`LICENSE`](LICENSE) for details.

<details>
<summary>The code is ugly and awful but it works *mostly* (click to vent)</summary>

We’re hardware engineers moonlighting as coders. Expect caffeine-driven hacks and the occasional refactor fiasco. Contributions and constructive feedback are *super* welcome!
</details>
