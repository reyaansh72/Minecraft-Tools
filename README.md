<div align="center">

# ⛏️ Minecraft Tools

### Explore, preview, search, and export Minecraft assets

An approachable desktop-assisted toolbox for Minecraft client JARs — from smooth panorama viewing to quick asset search and clean exports.

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/UI-Tkinter-2C5F2D" alt="Tkinter">
  <img src="https://img.shields.io/badge/Imaging-NumPy%20%2B%20Pillow-8A2BE2" alt="NumPy and Pillow">
  <img src="https://img.shields.io/badge/Exports-ZIP%20%7C%20TAR%20%7C%20Folder-orange" alt="ZIP, TAR, and folder export">
</p>

</div>

---

## ✨ Features

- **22 tools and actions** for extracting, searching, summarizing, and previewing Minecraft assets.
- **Automatic asset-layout detection** for modern `assets/minecraft/...` paths and common legacy JAR layouts.
- **Smooth panorama viewer** with automatic rotation, adjustable orientation, keyboard controls, and mouse look.
- **Image previewer** for inspecting PNG, JPEG, GIF, and BMP files without exporting first.
- **Asset search** across filenames and archive paths.
- **JAR summary** showing unpacked size and the most common file types.
- **Custom JAR paths** — enter a path such as `title/bg` to extract a specific asset folder.
- **Flexible output** — export selected assets as a ZIP, TAR, or regular folder.
- **Minecraft JAR download options** for Beta 1.8 and Alpha 1.2.6, or use an existing JAR.

## 🚀 Quick start

### Requirements

- Python 3 with Tkinter available (Tkinter is included with most standard Python installations).
- NumPy and Pillow for smooth panorama rendering.
- A Minecraft client JAR. The app can download one of its included legacy versions, or use a JAR you already have.

### Run

1. Download or clone this project.
2. Open a terminal in the project folder.
3. Install the image libraries:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   python app.py
   ```

5. Choose whether to download a supported JAR or use the existing `minecraft.jar`.
6. Select an operation from the menu and choose an output format.

## 🧰 Tools menu

| Option | Tool |
| ---: | --- |
| 1 | Panoramas |
| 2 | All textures |
| 3 | Music and sounds |
| 4 | Particles |
| 5 | Entity / mob textures |
| 6 | Block / terrain textures |
| 7 | All in-game assets |
| 8 | Custom path in the JAR |
| 9 | Panorama viewer |
| 10 | GUI |
| 11 | Item textures |
| 12 | Fonts |
| 13 | Language files |
| 14 | Environment textures |
| 15 | Miscellaneous textures |
| 16 | Armor textures |
| 17 | Art / painting textures |
| 18 | Blockstates |
| 19 | Models |
| 20 | Search assets by filename or path |
| 21 | Preview an image |
| 22 | JAR contents summary |

Some categories are only present in certain Minecraft versions. If a selected asset is not included in the JAR, the app reports that the path or files could not be found.

## 🌄 Panorama viewer

Choose **9. Panorama viewer**. When prompted for a panorama folder, press **Enter** to use the detected `title/bg` directory, or type a path such as `title/bg`.

| Control | Action |
| --- | --- |
| **Space** | Pause or resume continuous rotation |
| **← / →** | Nudge the camera view |
| **Mouse drag** | Look around smoothly |
| **H** | Flip the panorama horizontally |
| **V** | Flip the panorama vertically |
| **Esc** | Close the viewer |

The viewer continuously renders a perspective view using the four horizontal cube faces instead of stepping between still images. It supports `panorama0.png`–`panorama3.png` and `panorama_0.png`–`panorama_3.png` naming. Use **H** and **V** to toggle horizontal and vertical flips if a pack's images appear mirrored.

## 🔎 Search and preview

- **Search assets** looks for a case-insensitive phrase in extracted file names and paths. Matching files can then be exported in their original folder structure.
- **Preview an image** opens a file picker rooted in the extracted JAR and displays the selected image scaled to fit the window.
- **JAR contents summary** reports the number of files, total unpacked size, and up to 15 common file extensions.

## 📦 Export formats

After choosing an asset category, select one of:

- `zip` — creates `output.zip`
- `tar` — creates `output.tar`
- `folder` — creates an `output` directory

These output names are reused on the next export; existing output files or folders with those names may be replaced.

## ⚠️ Important notes

- The app extracts the chosen JAR into `tmp_extracted` while it runs, then removes that temporary directory.
- The original `minecraft.jar` is preserved after previews, summaries, and exports.
- Downloading a custom URL is marked not recommended in the app. Only use a trusted source.
- This is an unofficial community utility and is not affiliated with or endorsed by Mojang or Microsoft.

## 🛠️ Built with

Python's standard library (`zipfile`, `tarfile`, `urllib`, `ssl`, `tkinter`, and filesystem utilities), plus NumPy and Pillow for the panorama renderer.
