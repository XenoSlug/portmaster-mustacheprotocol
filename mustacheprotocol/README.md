# Mustache Protocol for PortMaster

Port of **Mustache Protocol: The Game** by Henry Cavill and Google for PortMaster-compatible Linux handheld gaming devices (muOS, ArkOS, AmberELEC, ROCKNIX, Knulli, etc.).

[![Download PortMaster Zip](https://img.shields.io/badge/Download-mustacheprotocol.zip-blue?style=for-the-badge&logo=github)](https://github.com/XenoSlug/portmaster-mustacheprotocol/releases/latest/download/mustacheprotocol.zip)
[![PortMaster RTR](https://img.shields.io/badge/PortMaster-Ready--to--Run-00f0ff?style=for-the-badge&logo=linux)](https://portmaster.games)
[![muOS Handheld](https://img.shields.io/badge/muOS-Compatible-ffd700?style=for-the-badge&logo=retroarch)](https://muos.dev)
[![Engine: Phaser 3](https://img.shields.io/badge/Engine-Phaser%203-ff007f?style=for-the-badge&logo=javascript)](https://phaser.io)
[![Runtime: retsurf](https://img.shields.io/badge/Runtime-retsurf%20(Servo%2FSDL2)-9d4edd?style=for-the-badge)](https://github.com/mxmgorin/retsurf)

> **"They’re erasing all the mustaches in the world. Only Henry Cavill can stop them."**

---

## About the Game

*Mustache Protocol: The Game* is a tongue-in-cheek, '80s-inspired 16-bit arcade action platformer created in a partnership between **Google** and actor **Henry Cavill** for the launch of the Googlebook and in support of **Movember**. 

Playing as Henry Cavill, you embark on a mission to stop rogue CGI artists and sinister high-tech mechs from digitally wiping facial hair from existence—a playful nod to his famous *Justice League* mustache meme. 

### Key Features
* **Three Action-Packed Stages:** Battle through Jersey Streets, the CGI Backlot, and the Machine Core.
* **Canine Companions:** Unlock Henry's faithful real-life dogs, **Kal** and **Baggins**, to aid you in combat.
* **Supercharged Powerups:** Unleash the **Arm Reload** buff, call in the **Tank Attack**, and deploy the **Works For Me** ultimate shield.
* **Multi-Phase Boss Battles:** Face off against giant mechanical claws, golf-carting art directors, and holographic overlords.
* **Original '80s Synthwave Soundtrack:** 9 custom audio tracks composed by **Mophonics**.
* **100% Free & Ready-to-Run:** No commercial files or purchases required; all assets are freely distributed by Google.

---

## Requirements

* A PortMaster-compatible 64-bit ARM Linux handheld (e.g., Anbernic RG35XX+, RG35XX H, RG35XX SP, RG40XX H/V, RG28XX, TrimUI Smart Pro, Powkiddy, etc.).
* Custom firmware with PortMaster support (e.g., **muOS**, **ArkOS**, **AmberELEC**, **ROCKNIX**, **Knulli**).
* PortMaster **retsurf** runtime (automatically installed via PortMaster or downloadable from PortMaster Manage Ports).

---

## Installation Instructions

### Option 1: PortMaster Autoinstall (Recommended)

1. Download [`mustacheprotocol.zip`](https://github.com/XenoSlug/portmaster-mustacheprotocol/releases/latest/download/mustacheprotocol.zip) from the latest release.
2. Connect your handheld's SD card to your computer.
3. Drop `mustacheprotocol.zip` into the autoinstall directory:
   * **muOS:** `/MUOS/PortMaster/autoinstall/`
   * **ArkOS / AmberELEC / Knulli:** `/roms/ports/autoinstall/` (or `/userdata/roms/ports/autoinstall/`)
4. Insert the SD card back into your handheld and launch **PortMaster**.
5. PortMaster will automatically extract the files, setup permissions, scrape the box art, and install the game to your Ports menu.

---

### Option 2: Manual Installation

If you prefer extracting manually:

1. Download [`mustacheprotocol.zip`](https://github.com/XenoSlug/portmaster-mustacheprotocol/releases/latest/download/mustacheprotocol.zip).
2. Extract the archive directly to the root of your SD card (SD1 or SD2):
   ```text
   sdcard/
   ├── ROMS/
   │   └── Ports/
   │       └── Mustache Protocol.sh
   └── ports/
       └── mustacheprotocol/
           ├── port.json
           ├── gameinfo.xml
           ├── Mustache Protocol.gptk
           ├── cover.png
           ├── screenshot.png
           ├── README.md
           ├── licenses/
           │   └── LICENSE
           └── www/ (Complete offline game assets, audio, and videos)
   ```
3. On your handheld, ensure **retsurf** is installed from PortMaster (under *Manage Ports* > *retsurf*).
4. Launch **Mustache Protocol** from your handheld's Ports / Content Explorer.

---

## Controls

The port is mapped with an authentic 16-bit arcade button layout via `gptokeyb` and standard Gamepad API bindings:

| Handheld Button | Key Binding | Action |
| :--- | :--- | :--- |
| **D-Pad / Left Analog** | <kbd>▲</kbd> <kbd>▼</kbd> <kbd>◀</kbd> <kbd>▶</kbd> / <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> | Move / Crouch / Aim |
| **A** | <kbd>Space</kbd> | Jump / Dialogue Confirm |
| **X** | <kbd>J</kbd> | Attack (Sword Slash / Melee) |
| **Y** | <kbd>K</kbd> | Tank Attack (Powerup) |
| **B** | <kbd>L</kbd> | Works For Me (Shield / Powerup) |
| **L1 / L2** | <kbd>O</kbd> | Arm Reload (Strength Buff) |
| **R1 / R2** | <kbd>I</kbd> | Ultimate Ability |
| **Select** | <kbd>B</kbd> | Warp to Boss Arena (Shortcut) |
| **Start** | <kbd>Esc</kbd> | Pause Menu / Skip Cutscenes |

---

## How It Works (Technical Overview)

* **Phaser 3 HTML5 Canvas:** The core game runs on the Phaser 3 framework using WebGL / 2D Canvas rendering and Web Audio.
* **Embedded retsurf Runtime:** Built on Mozilla's Servo browser engine and SDL2, `retsurf` provides hardware-accelerated rendering on lightweight Linux handhelds without desktop browser overhead.
* **Background Localhost Server:** Because browsers restrict `<script type="module">` over raw `file://` protocols, the launch script spins up a tiny background daemon (`busybox httpd` or Python 3, built into muOS) on `127.0.0.1:8089` and terminates it cleanly when exiting the game.

---

## Soundtrack

Original chiptune soundtrack and audio design composed by **Mophonics**:

| Track | In-Game Scene |
| :--- | :--- |
| `mophonics-l1-theme.mp3` | Stage 1: Jersey Streets |
| `mophonics-l1-boss.mp3` | Stage 1 Boss: The Headmaster |
| `mophonics-l2-theme.mp3` | Stage 2: CGI Backlot |
| `mophonics-l2-boss.mp3` | Stage 2 Boss: Golf Cart Terror |
| `mophonics-l3-theme.mp3` | Stage 3: The Machine Core |
| `mophonics-l3-boss.mp3` | Stage 3 Boss: The Final Artist |
| `mophonics-tank-attack.mp3` | Tank Attack Powerup Groove |
| `mophonics-victory.mp3` | Stage Cleared & Celebration |
| `mophonics-death.mp3` | Game Over / Retry |

---

## Credits & Acknowledgments

* **Henry Cavill**: Creator, concept, voice & likeness, protagonist, and creative partner with Google.
* **Google / Googlebook Team**: Production, game development, and the Antigravity integration.
* **Movember Foundation**: The men's health charity supported by the campaign.
* **Mophonics**: Original chiptune synth soundtrack, theme songs, and sound design.
* **Luis Montes (@monteslu)**: Creator of `jsgamelauncher` and pioneer of web-to-handheld compatibility.
* **Maxim Gorin (@mxmgorin)**: Creator of `retsurf`, the Servo/SDL2 browser engine tailored for retro handhelds.
* **The Servo Project & Contributors**: The high-performance, memory-safe browser engine written in Rust.
* **The PortMaster Project & HarbourMaster Team**: ChristianHaitian, Cebion, kloptops, and the community of porters for maintaining the handheld porting ecosystem.
* **muOS Team (MustardOS)**: Custom Linux operating system for Anbernic H700 retro handheld devices.
* **Phaser Studio Inc. (Richard Davey / Photon Storm)**: Creators of the Phaser 3 HTML5 Game Engine.
* **Matter.js (William Bithrey)**: 2D physics engine used in Phaser.
* **Font Designers**:
  * **Outfit**: Rodrigo Fuenzalida & Omnibus-Type (SIL Open Font License 1.1)
  * **Press Start 2P**: CodeMan38 / Cody Boisclair (SIL Open Font License 1.1)
  * **Silkscreen**: Jason Kottke (SIL Open Font License 1.1)
* **Port Packaging**: Packaged for PortMaster by **XenoSlug** and **Google Antigravity**.

---

## License

* **Game Content & Assets:** © 2026 Google LLC & Henry Cavill. All rights reserved. Made available freely for promotional and charity play.
* **Port Packaging & Scripts:** Released under the [MIT License](mustacheprotocol/licenses/LICENSE).
* **Fonts:** Distributed under the [SIL Open Font License 1.1](mustacheprotocol/www/fonts/fonts.css).
