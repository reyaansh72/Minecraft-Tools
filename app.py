import os
import zipfile
import tarfile
import shutil
import time
import urllib.request
import ssl
import tkinter as tk
from collections import Counter
from tkinter import filedialog


# ============================================================
# MINECRAFT TOOLS
# ============================================================

APP_NAME = "Minecraft Tools"

jarfile = "minecraft.jar"
extracted_dir = "tmp_extracted"
PANORAMA_FRAME_INTERVAL_MS = 33
PANORAMA_ROTATION_SPEED = 0.12
PANORAMA_RENDER_WIDTH = 400


def render_panorama_frame(
    face_arrays,
    yaw,
    width,
    height,
    numpy,
    flip_horizontal=False,
    flip_vertical=False
):
    aspect_ratio = width / height
    view_scale = numpy.tan(numpy.deg2rad(35))

    screen_x = (
        (numpy.arange(width, dtype=numpy.float32) + 0.5) /
        width * 2 - 1
    ) * view_scale * aspect_ratio
    screen_y = (
        1 -
        (numpy.arange(height, dtype=numpy.float32) + 0.5) /
        height * 2
    ) * view_scale
    x, y = numpy.meshgrid(screen_x, screen_y)

    sin_yaw = numpy.sin(yaw)
    cos_yaw = numpy.cos(yaw)
    ray_x = sin_yaw + x * cos_yaw
    ray_y = y
    ray_z = cos_yaw - x * sin_yaw

    abs_x = numpy.abs(ray_x)
    abs_z = numpy.abs(ray_z)
    face_indices = numpy.where(
        abs_x >= abs_z,
        numpy.where(ray_x >= 0, 1, 3),
        numpy.where(ray_z >= 0, 0, 2)
    )

    major_axis = numpy.where(
        (face_indices == 1) | (face_indices == 3),
        abs_x,
        abs_z
    )
    coordinate_u = numpy.where(
        face_indices == 0,
        ray_x,
        numpy.where(
            face_indices == 1,
            -ray_z,
            numpy.where(
                face_indices == 2,
                -ray_x,
                ray_z
            )
        )
    )
    face_u = (coordinate_u / major_axis + 1) * 0.5
    face_v = 0.5 - ray_y / major_axis

    face_v = numpy.clip(face_v, 0, 1)

    face_height, face_width = face_arrays.shape[1:3]
    pixel_x = numpy.clip(
        (face_u * face_width).astype(numpy.int32),
        0,
        face_width - 1
    )
    pixel_y = numpy.clip(
        (face_v * face_height).astype(numpy.int32),
        0,
        face_height - 1
    )
    frame = face_arrays[
        face_indices,
        pixel_y,
        pixel_x
    ]
    if flip_horizontal:
        frame = numpy.flip(frame, axis=1)
    if flip_vertical:
        frame = numpy.flip(frame, axis=0)
    return frame


def first_existing_path(*paths):
    for path in paths:
        if os.path.exists(os.path.join(extracted_dir, path)):
            return path
    return paths[0]


def archive_path(path):
    normalized_path = os.path.normpath(
        path.replace("/", os.sep).replace("\\", os.sep)
    )

    if normalized_path == extracted_dir:
        return ""

    extracted_prefix = extracted_dir + os.sep
    if normalized_path.startswith(extracted_prefix):
        normalized_path = normalized_path[len(extracted_prefix):]

    if os.path.isabs(normalized_path) or normalized_path == os.pardir:
        raise ValueError("Enter a path relative to the JAR contents.")

    if normalized_path.startswith(os.pardir + os.sep):
        raise ValueError("Enter a path relative to the JAR contents.")

    return normalized_path


# ============================================================
# FORMATTING
# ============================================================

def format_bytes(size):
    if size < 1024:
        return f"{size:.0f} B"
    if size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"
    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"
    return f"{size / (1024 ** 3):.2f} GB"


def format_time(seconds):
    seconds = int(seconds)

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    seconds %= 60

    if minutes < 60:
        return f"{minutes}m {seconds}s"

    hours = minutes // 60
    minutes %= 60

    return f"{hours}h {minutes}m"


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(url, output_path, chunk_size=1024 * 64):
    output_dir = os.path.dirname(output_path)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"\nDownloading: {url}")
    print(f"Saving to:   {output_path}")

    try:
        ssl_context = ssl.create_default_context()

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Minecraft-Tools/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            context=ssl_context
        ) as response:

            total_size = response.headers.get(
                "Content-Length"
            )

            if total_size:
                total_size = int(total_size)
            else:
                total_size = None

            downloaded = 0
            start_time = time.time()

            with open(output_path, "wb") as file:
                while True:
                    chunk = response.read(chunk_size)

                    if not chunk:
                        break

                    file.write(chunk)
                    downloaded += len(chunk)

                    elapsed = time.time() - start_time

                    if elapsed > 0:
                        speed = downloaded / elapsed
                    else:
                        speed = 0

                    if total_size:
                        percent = (
                            downloaded /
                            total_size *
                            100
                        )

                        if speed > 0:
                            remaining = (
                                total_size -
                                downloaded
                            )
                            eta = remaining / speed
                        else:
                            eta = 0

                        bar_length = 30

                        filled = int(
                            bar_length *
                            downloaded /
                            total_size
                        )

                        bar = (
                            "█" * filled +
                            "░" *
                            (bar_length - filled)
                        )

                        print(
                            f"\r[{bar}] "
                            f"{percent:6.2f}% "
                            f"{format_bytes(downloaded)}/"
                            f"{format_bytes(total_size)} "
                            f"{format_bytes(speed)}/s "
                            f"ETA {format_time(eta)}",
                            end="",
                            flush=True
                        )

                    else:
                        print(
                            f"\rDownloaded "
                            f"{format_bytes(downloaded)} "
                            f"at {format_bytes(speed)}/s "
                            f"Elapsed {format_time(elapsed)}",
                            end="",
                            flush=True
                        )

        print("\nDownload complete!")
        print(f"File: {output_path}")
        return True

    except Exception as error:
        print("\nDownload failed!")
        print(f"Error: {error}")

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

        return False


# ============================================================
# PANORAMA FILE DETECTION
# ============================================================

def find_panorama_files(folder):
    """
    Loads the four horizontal panorama faces in either naming scheme:

    Modern:
        panorama_0.png through panorama_3.png

    Old:
        panorama0.png through panorama3.png

    Modern naming is preferred if all four files exist.
    Otherwise the old naming scheme is tried.
    """

    modern_files = [
        os.path.join(
            folder,
            f"panorama_{i}.png"
        )
        for i in range(4)
    ]

    old_files = [
        os.path.join(
            folder,
            f"panorama{i}.png"
        )
        for i in range(4)
    ]

    # --------------------------------------------------------
    # Modern format
    # --------------------------------------------------------

    if all(
        os.path.isfile(path)
        for path in modern_files
    ):
        return modern_files, "panorama_0.png"

    # --------------------------------------------------------
    # Old format
    # --------------------------------------------------------

    if all(
        os.path.isfile(path)
        for path in old_files
    ):
        return old_files, "panorama0.png"

    return None, None


def preview_image_folder(folder):
    try:
        from PIL import Image, ImageTk
    except ImportError as error:
        print("ERROR: Image preview requires Pillow.")
        print("Install it with: python -m pip install -r requirements.txt")
        print(error)
        input("Press Enter to return...")
        return

    root = tk.Tk()
    root.withdraw()

    filepath = filedialog.askopenfilename(
        parent=root,
        title="Choose a Minecraft image to preview",
        initialdir=folder,
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("All files", "*.*")
        ]
    )

    if not filepath:
        root.destroy()
        return

    try:
        image = Image.open(filepath).convert("RGBA")
    except OSError as error:
        root.destroy()
        print(f"ERROR: Could not open image: {filepath}")
        print(error)
        input("Press Enter to return...")
        return

    root.deiconify()
    root.title(f"Minecraft Tools - {os.path.basename(filepath)}")
    root.geometry("900x700")
    root.minsize(400, 300)

    label = tk.Label(
        root,
        text=(
            f"{os.path.relpath(filepath, folder)}  •  "
            f"{image.width} × {image.height}"
        ),
        anchor="w",
        padx=12,
        pady=8
    )
    label.pack(fill="x")

    canvas = tk.Canvas(root, bg="#171717", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    def draw_preview(event=None):
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 2 or height < 2:
            return

        preview = image.copy()
        preview.thumbnail(
            (width, height),
            Image.Resampling.LANCZOS
        )
        display_image = ImageTk.PhotoImage(preview)
        canvas.delete("all")
        canvas.create_image(
            width // 2,
            height // 2,
            image=display_image,
            anchor="center"
        )
        canvas.image = display_image

    canvas.bind("<Configure>", draw_preview)
    root.mainloop()


# ============================================================
# PANORAMA VIEWER
# ============================================================

def panorama_viewer():
    print("\n" + "=" * 50)
    print("MINECRAFT TOOLS - PANORAMA VIEWER")
    print("=" * 50)

    print("\nEnter the folder containing the panorama files.")
    print("Supported formats:")
    print("  panorama_0.png - panorama_3.png")
    print("  panorama0.png  - panorama3.png")

    print("\nExample:")
    print(
        "title/bg (or assets/minecraft/textures/gui/title/background)"
    )

    panorama_path = input(
        "\nPanorama folder path (Enter for title/bg): "
    ).strip().strip('"')

    if not panorama_path:
        panorama_path = os.path.join(
            extracted_dir,
            first_existing_path(
                "title/bg",
                os.path.join(
                    "assets",
                    "minecraft",
                    "textures",
                    "gui",
                    "title",
                    "background"
                )
            )
        )

    elif not os.path.isabs(panorama_path) and not os.path.exists(panorama_path):
        try:
            panorama_path = os.path.join(
                extracted_dir,
                archive_path(panorama_path)
            )
        except ValueError as error:
            print(f"ERROR: {error}")
            input("Press Enter to return...")
            return

    panorama_path = os.path.abspath(panorama_path)

    if not os.path.isdir(panorama_path):
        print("ERROR: Folder does not exist.")
        print(panorama_path)
        input("Press Enter to return...")
        return

    panorama_files, naming = find_panorama_files(
        panorama_path
    )

    if panorama_files is None:
        print(
            "\nERROR: Could not find all four horizontal panorama files."
        )
        print("\nTried:")
        print("  panorama_0.png - panorama_3.png")
        print("  panorama0.png  - panorama3.png")
        input("\nPress Enter to return...")
        return

    print(
        f"\nFound panorama using {naming} naming."
    )
    print("Opening Panorama Viewer...")

    try:
        import numpy
        from PIL import Image, ImageTk
    except ImportError as error:
        print("ERROR: Smooth panorama viewing requires Pillow and NumPy.")
        print("Install them with: python -m pip install -r requirements.txt")
        print(error)
        input("Press Enter to return...")
        return

    face_arrays = []
    try:
        loaded_faces = [
            Image.open(filepath).convert("RGB")
            for filepath in panorama_files
        ]
        face_size = min(
            512,
            *(min(image.size) for image in loaded_faces)
        )
        face_arrays = numpy.stack([
            numpy.asarray(
                image.resize(
                    (face_size, face_size),
                    Image.Resampling.BILINEAR
                ),
                dtype=numpy.uint8
            )
            for image in loaded_faces
        ])
    except Exception as error:
        print("ERROR: Could not load panorama faces.")
        print(error)
        input("Press Enter to return...")
        return

    try:
        root = tk.Tk()
    except Exception as error:
        print("ERROR: Could not create viewer window.")
        print(error)
        input("Press Enter to return...")
        return

    root.title(
        "Minecraft Tools - Panorama Viewer"
    )

    root.geometry("1000x650")
    root.minsize(700, 500)

    # --------------------------------------------------------
    # Main canvas
    # --------------------------------------------------------

    canvas = tk.Canvas(
        root,
        bg="black",
        highlightthickness=0
    )

    canvas.pack(
        fill="both",
        expand=True
    )

    # --------------------------------------------------------
    # Viewer state
    # --------------------------------------------------------

    yaw = 0.0
    last_x = None
    auto_rotation_enabled = True
    flip_horizontal = False
    flip_vertical = False
    last_frame_time = time.perf_counter()

    # --------------------------------------------------------
    # Draw panorama face
    # --------------------------------------------------------

    def draw():
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if (
            width <= 1 or
            height <= 1
        ):
            root.after(
                50,
                draw
            )
            return

        render_width = min(width, PANORAMA_RENDER_WIDTH)
        render_height = max(
            1,
            int(render_width * height / width)
        )
        frame = render_panorama_frame(
            face_arrays,
            yaw,
            render_width,
            render_height,
            numpy,
            flip_horizontal,
            flip_vertical
        )
        display_image = Image.fromarray(frame).resize(
            (width, height),
            Image.Resampling.BILINEAR
        )
        display_image = ImageTk.PhotoImage(display_image)

        canvas.create_image(
            0,
            0,
            image=display_image,
            anchor="nw"
        )

        canvas.image = display_image

        # ----------------------------------------------------
        # Top information
        # ----------------------------------------------------

        canvas.create_rectangle(
            10,
            10,
            410,
            100,
            fill="black",
            outline="white"
        )

        canvas.create_text(
            20,
            27,
            text="Minecraft Tools",
            fill="white",
            anchor="w",
            font=("Arial", 14, "bold")
        )

        canvas.create_text(
            20,
            52,
            text=f"Yaw {int((yaw % (2 * numpy.pi)) * 180 / numpy.pi)}°",
            fill="white",
            anchor="w",
            font=("Arial", 11)
        )

        canvas.create_text(
            170,
            52,
            text=(
                "Auto: On" if auto_rotation_enabled else "Auto: Off"
            ),
            fill="white",
            anchor="w",
            font=("Arial", 11)
        )

        canvas.create_text(
            20,
            78,
            text=(
                f"Flip H: {'On' if flip_horizontal else 'Off'}"
                f"   Flip V: {'On' if flip_vertical else 'Off'}"
            ),
            fill="white",
            anchor="w",
            font=("Arial", 11)
        )

        # ----------------------------------------------------
        # Bottom controls
        # ----------------------------------------------------

        canvas.create_rectangle(
            10,
            height - 50,
            690,
            height - 10,
            fill="black",
            outline="white"
        )

        canvas.create_text(
            20,
            height - 30,
            text=(
                "← / → or drag: rotate | Space: auto | H/V: flip"
            ),
            fill="white",
            anchor="w",
            font=("Arial", 11)
        )

    # --------------------------------------------------------
    # Rotate camera
    # --------------------------------------------------------

    def rotate_camera(direction):
        nonlocal yaw, last_frame_time
        yaw += direction * 0.18
        last_frame_time = time.perf_counter()
        draw()

    # --------------------------------------------------------
    # Keyboard controls
    # --------------------------------------------------------

    def key_press(event):
        nonlocal auto_rotation_enabled, last_frame_time, flip_horizontal, flip_vertical

        if event.keysym == "Left":
            rotate_camera(-1)

        elif event.keysym == "Right":
            rotate_camera(1)

        elif event.keysym == "space":
            auto_rotation_enabled = not auto_rotation_enabled
            last_frame_time = time.perf_counter()
            draw()

        elif event.keysym.lower() == "h":
            flip_horizontal = not flip_horizontal
            draw()

        elif event.keysym.lower() == "v":
            flip_vertical = not flip_vertical
            draw()

        elif event.keysym == "Escape":
            root.destroy()

    def animate():
        nonlocal yaw, last_frame_time
        now = time.perf_counter()

        if auto_rotation_enabled:
            elapsed = min(now - last_frame_time, 0.1)
            yaw += elapsed * PANORAMA_ROTATION_SPEED

        last_frame_time = now
        draw()
        root.after(PANORAMA_FRAME_INTERVAL_MS, animate)

    # --------------------------------------------------------
    # Mouse controls
    # --------------------------------------------------------

    def mouse_down(event):
        nonlocal last_x
        last_x = event.x

    def mouse_drag(event):
        nonlocal last_x, yaw, last_frame_time

        if last_x is None:
            last_x = event.x
            return

        difference = event.x - last_x
        yaw -= difference * 0.005
        last_x = event.x
        last_frame_time = time.perf_counter()
        draw()

    def mouse_up(event):
        nonlocal last_x
        last_x = None

    canvas.bind(
        "<Button-1>",
        mouse_down
    )

    canvas.bind(
        "<B1-Motion>",
        mouse_drag
    )

    canvas.bind(
        "<ButtonRelease-1>",
        mouse_up
    )

    root.bind(
        "<Key>",
        key_press
    )

    canvas.bind(
        "<Configure>",
        lambda event: draw()
    )

    canvas.focus_set()

    draw()
    root.after(PANORAMA_FRAME_INTERVAL_MS, animate)

    root.mainloop()

    print("Panorama Viewer closed.")


# ============================================================
# START PROGRAM
# ============================================================

print("=" * 50)
print(APP_NAME)
print("=" * 50)

print(
    "\nMake sure minecraft.jar is in the same directory "
    "as this script."
)

input("Press Enter to continue...")


# ============================================================
# DOWNLOAD MINECRAFT JAR
# ============================================================

choice3 = input(
    "\nDownload a Minecraft.jar from the Internet "
    "or keep existing? (y/n): "
).lower().strip()


if choice3 == "y":

    print("\n1. Minecraft Beta 1.8")
    print("2. Minecraft Alpha 1.2.6")
    print("3. Custom URL (Not Recommended)")

    choice4 = input(
        "Enter your choice (1-3): "
    ).strip()

    if choice4 == "1":

        url = (
            "https://piston-data.mojang.com/v1/objects/"
            "3139e9c29b2c74f59ea04de760ac2af5bc21b410/"
            "client.jar"
        )

        if not download_file(
            url,
            jarfile
        ):
            input("Press Enter to exit...")
            raise SystemExit

    elif choice4 == "2":

        url = (
            "https://piston-data.mojang.com/v1/objects/"
            "a68c817afd6c05c253ba5462287c2c19bbb57935/"
            "client.jar"
        )

        if not download_file(
            url,
            jarfile
        ):
            input("Press Enter to exit...")
            raise SystemExit

    elif choice4 == "3":

        url = input(
            "Enter the URL of the Minecraft.jar file: "
        ).strip()

        if not download_file(
            url,
            jarfile
        ):
            input("Press Enter to exit...")
            raise SystemExit

    else:

        print("ERROR: Invalid choice!")
        input("Press Enter to exit...")
        raise SystemExit

else:

    print("Keeping existing minecraft.jar file.")


# ============================================================
# CHECK JAR
# ============================================================

if not os.path.exists(jarfile):

    print(
        "\nERROR: minecraft.jar was not found!"
    )

    input("Press Enter to exit...")
    raise SystemExit


# ============================================================
# EXTRACT JAR
# ============================================================

if os.path.exists(extracted_dir):
    shutil.rmtree(extracted_dir)

print(
    "\nExtracting all files from minecraft.jar..."
)

try:

    with zipfile.ZipFile(
        jarfile,
        "r"
    ) as zip_ref:

        zip_ref.extractall(
            extracted_dir
        )

except zipfile.BadZipFile:

    print(
        "ERROR: minecraft.jar is not a valid "
        "ZIP/JAR file."
    )

    input("Press Enter to exit...")
    raise SystemExit


print("Extraction complete.")


# ============================================================
# MAIN MENU
# ============================================================

print("\n" + "=" * 54)
print("  MINECRAFT TOOLS  |  ASSET WORKBENCH")
print("=" * 54)
print("\nEXTRACT")
print(" 1  Panoramas                 2  All textures")
print(" 3  Music and sounds          4  Particles")
print(" 5  Entity / mob textures     6  Block / terrain textures")
print(" 7  All in-game assets        8  Custom JAR path")
print("\nASSET CATEGORIES")
print("10  GUI                       11  Item textures")
print("12  Fonts                     13  Language files")
print("14  Environment textures      15  Miscellaneous textures")
print("16  Armor textures            17  Art / paintings")
print("18  Blockstates               19  Models")
print("\nVIEW & UTILITIES")
print(" 9  Panorama viewer          20  Search assets")
print("21  Preview an image          22  JAR contents summary")
print("\n" + "-" * 54)

choice = input(
    "\nEnter your choice (1-22): "
).strip()


# ============================================================
# OPTION 9
# ============================================================

if choice == "9":

    panorama_viewer()

    shutil.rmtree(
        extracted_dir,
        ignore_errors=True
    )

    print("\nDone!")
    raise SystemExit


if choice == "21":
    preview_image_folder(extracted_dir)
    shutil.rmtree(extracted_dir, ignore_errors=True)
    print("\nPreview closed.")
    raise SystemExit


if choice == "22":
    file_count = 0
    total_size = 0
    extensions = Counter()

    for root, dirs, files in os.walk(extracted_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_count += 1
            total_size += os.path.getsize(filepath)
            extension = os.path.splitext(filename)[1].lower() or "[no extension]"
            extensions[extension] += 1

    print("\n" + "=" * 54)
    print("JAR CONTENTS SUMMARY")
    print("=" * 54)
    print(f"Files: {file_count:,}")
    print(f"Unpacked size: {format_bytes(total_size)}")
    print("\nMost common file types:")
    for extension, count in extensions.most_common(15):
        print(f"  {extension:<18} {count:>8,}")

    shutil.rmtree(extracted_dir, ignore_errors=True)
    print("\nOriginal minecraft.jar was kept.")
    input("\nPress Enter to exit...")
    raise SystemExit


# ============================================================
# ASSET SELECTION
# ============================================================

selected_files = None
selected_roots = None


if choice == "1":

    selected_path = first_existing_path(
        os.path.join(
            "assets",
            "minecraft",
            "textures",
            "gui",
            "title",
            "background"
        ),
        os.path.join("title", "bg")
    )

    # --------------------------------------------------------
    # Automatically detect modern or old panorama names.
    # --------------------------------------------------------

    selected_path_full = os.path.join(
        extracted_dir,
        selected_path
    )

    panorama_files, naming = find_panorama_files(
        selected_path_full
    )

    if panorama_files is not None:

        selected_files = [
            os.path.basename(path)
            for path in panorama_files
        ]

        print(
            f"\nDetected panorama format: {naming}"
        )

    else:

        print(
            "\nERROR: Could not find all four horizontal panorama files."
        )

        print("Tried:")
        print("  panorama_0.png - panorama_3.png")
        print("  panorama0.png  - panorama3.png")

        shutil.rmtree(
            extracted_dir,
            ignore_errors=True
        )

        input("Press Enter to exit...")
        raise SystemExit


elif choice == "2":

    modern_textures = os.path.join(
        "assets",
        "minecraft",
        "textures"
    )

    if os.path.isdir(os.path.join(extracted_dir, modern_textures)):
        selected_path = modern_textures
    else:
        selected_path = ""
        selected_roots = [
            "terrain.png",
            "particles.png",
            "gui",
            "item",
            "mob",
            "armor",
            "art",
            "environment",
            "misc",
            "font",
            "title",
            "achievement"
        ]


elif choice == "3":

    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "sounds"),
        "sound",
        "sounds"
    )


elif choice == "4":

    selected_path = first_existing_path(
        "assets/minecraft/particles",
        "particles.png"
    )
    if os.path.isfile(os.path.join(extracted_dir, selected_path)):
        selected_files = [os.path.basename(selected_path)]
        selected_path = os.path.dirname(selected_path)


elif choice == "5":

    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "entity"),
        "mob"
    )


elif choice == "6":

    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "block"),
        os.path.join("assets", "minecraft", "textures", "blocks"),
        "terrain.png"
    )
    if os.path.isfile(os.path.join(extracted_dir, selected_path)):
        selected_files = [os.path.basename(selected_path)]
        selected_path = os.path.dirname(selected_path)


elif choice == "7":

    modern_assets = os.path.join("assets", "minecraft")

    if os.path.isdir(os.path.join(extracted_dir, modern_assets)):
        selected_path = modern_assets
    else:
        selected_path = ""
        selected_roots = [
            "terrain.png",
            "particles.png",
            "gui",
            "item",
            "mob",
            "armor",
            "art",
            "environment",
            "misc",
            "font",
            "title",
            "achievement",
            "lang",
            "sound",
            "sounds",
            "music"
        ]


elif choice == "8":

    try:
        selected_path = archive_path(input(
            "\nEnter the path within the JAR (e.g. title/bg): "
        ).strip().strip('"'))
    except ValueError as error:
        print(f"\nERROR: {error}")
        shutil.rmtree(extracted_dir, ignore_errors=True)
        input("Press Enter to exit...")
        raise SystemExit


elif choice == "10":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "gui"),
        "gui"
    )


elif choice == "11":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "item"),
        os.path.join("assets", "minecraft", "textures", "items"),
        "item"
    )


elif choice == "12":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "font"),
        os.path.join("assets", "minecraft", "textures", "font"),
        "font"
    )


elif choice == "13":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "lang"),
        "lang"
    )


elif choice == "14":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "environment"),
        "environment"
    )


elif choice == "15":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "misc"),
        "misc"
    )


elif choice == "16":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "entity", "armor"),
        os.path.join("assets", "minecraft", "textures", "models", "armor"),
        "armor"
    )


elif choice == "17":
    selected_path = first_existing_path(
        os.path.join("assets", "minecraft", "textures", "painting"),
        "art"
    )


elif choice == "18":
    selected_path = os.path.join(
        "assets",
        "minecraft",
        "blockstates"
    )


elif choice == "19":
    selected_path = os.path.join(
        "assets",
        "minecraft",
        "models"
    )


elif choice == "20":
    search_term = input(
        "\nSearch file names or paths for (e.g. creeper, panorama, .ogg): "
    ).strip().casefold()

    if not search_term:
        print("\nERROR: Enter a search term.")
        shutil.rmtree(extracted_dir, ignore_errors=True)
        input("Press Enter to exit...")
        raise SystemExit

    selected_path = ""
    selected_files = []

    for root, dirs, files in os.walk(extracted_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            relative_path = os.path.relpath(filepath, extracted_dir)

            if search_term in relative_path.casefold():
                selected_files.append(relative_path)

    print(f"\nFound {len(selected_files):,} matching file(s).")
    if not selected_files:
        shutil.rmtree(extracted_dir, ignore_errors=True)
        input("No matching assets found. Press Enter to exit...")
        raise SystemExit

    for relative_path in selected_files[:40]:
        print(f"  {relative_path}")
    if len(selected_files) > 40:
        print(f"  ... and {len(selected_files) - 40:,} more")


else:

    print("\nERROR: Invalid choice!")

    shutil.rmtree(
        extracted_dir,
        ignore_errors=True
    )

    input("Press Enter to exit...")
    raise SystemExit


# ============================================================
# PATHS
# ============================================================

base_path = os.path.join(
    extracted_dir,
    selected_path
)


# ============================================================
# OUTPUT FORMAT
# ============================================================

print("\nChoose output format:")
print("  zip    - compressed ZIP archive")
print("  tar    - TAR archive")
print("  folder - regular output directory")

choice2 = input(
    "Create ZIP, TAR, or folder? (zip/tar/folder): "
).lower().strip()


if choice2 not in [
    "zip",
    "tar",
    "folder"
]:

    print("\nERROR: Invalid output format!")
    print(
        "Please choose: zip, tar, or folder."
    )

    shutil.rmtree(
        extracted_dir,
        ignore_errors=True
    )

    input("Press Enter to exit...")
    raise SystemExit


# ============================================================
# FIND FILES
# ============================================================

print("\nFinding selected files...")

files_to_export = []


if selected_roots is not None:

    for relative_path in selected_roots:
        file_path = os.path.join(extracted_dir, relative_path)

        if os.path.isfile(file_path):
            files_to_export.append(file_path)
        elif os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for filename in files:
                    files_to_export.append(
                        os.path.join(root, filename)
                    )


elif selected_files is not None:

    for filename in selected_files:

        file_path = os.path.join(
            base_path,
            filename
        )

        if os.path.isfile(file_path):

            files_to_export.append(
                file_path
            )

        else:

            print(
                f"WARNING: File not found: "
                f"{filename}"
            )


else:

    if not os.path.isdir(base_path):

        print(
            "\nERROR: Selected path does not exist:"
        )

        print(base_path)

        shutil.rmtree(
            extracted_dir,
            ignore_errors=True
        )

        input("Press Enter to exit...")
        raise SystemExit

    for root, dirs, files in os.walk(
        base_path
    ):

        for filename in files:

            file_path = os.path.join(
                root,
                filename
            )

            files_to_export.append(
                file_path
            )


print(
    f"Found {len(files_to_export)} files."
)


if not files_to_export:

    print("\nERROR: Nothing to export.")

    shutil.rmtree(
        extracted_dir,
        ignore_errors=True
    )

    input("Press Enter to exit...")
    raise SystemExit


# ============================================================
# ZIP
# ============================================================

if choice2 == "zip":

    zip_filename = "output.zip"

    with zipfile.ZipFile(
        zip_filename,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for file_path in files_to_export:

            arcname = os.path.relpath(
                file_path,
                base_path
            )

            zipf.write(
                file_path,
                arcname
            )

    print(
        f"\nCreated {zip_filename} successfully."
    )


# ============================================================
# TAR
# ============================================================

elif choice2 == "tar":

    tar_filename = "output.tar"

    with tarfile.open(
        tar_filename,
        "w"
    ) as tar:

        for file_path in files_to_export:

            arcname = os.path.relpath(
                file_path,
                base_path
            )

            tar.add(
                file_path,
                arcname=arcname
            )

    print(
        f"\nCreated {tar_filename} successfully."
    )


# ============================================================
# FOLDER
# ============================================================

elif choice2 == "folder":

    output_folder = "output"

    if os.path.exists(
        output_folder
    ):
        shutil.rmtree(
            output_folder
        )

    os.makedirs(
        output_folder
    )

    for file_path in files_to_export:

        relative_path = os.path.relpath(
            file_path,
            base_path
        )

        destination = os.path.join(
            output_folder,
            relative_path
        )

        destination_directory = os.path.dirname(
            destination
        )

        if destination_directory:

            os.makedirs(
                destination_directory,
                exist_ok=True
            )

        shutil.copy2(
            file_path,
            destination
        )

    print(
        f"\nCreated {output_folder} folder successfully."
    )


# ============================================================
# CLEANUP
# ============================================================

shutil.rmtree(
    extracted_dir,
    ignore_errors=True
)


print("\nExport complete. Your original Minecraft JAR was kept.")
input("Press Enter to exit...")