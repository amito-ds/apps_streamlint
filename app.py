import os
import re
import streamlit as st
import zipfile
from PIL import Image
import io
from math import ceil

def alphanumeric_key(filename):
    """
    Convert filename into a list of string and integer chunks for "natural" sorting.
    E.g. "10.png" -> ['','10',''] + ['.png'] -> [ '', 10, '' , '.png' ].
    """
    base, ext = os.path.splitext(filename)
    parts = re.split(r'(\d+)', base)
    return [int(p) if p.isdigit() else p.lower() for p in parts] + [ext.lower()]

def main():
    st.title("Combine 4 Images per PDF Page")

    uploaded_zip = st.file_uploader("Upload a ZIP containing images", type=["zip"])
    if uploaded_zip is not None:
        try:
            with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff")

                # Raw list of files from ZIP
                all_files = zip_ref.namelist()
                st.write("**Files in ZIP (unsorted):**", all_files)

                # Keep only valid image files
                image_files = [
                    f for f in all_files
                    if f.lower().endswith(valid_extensions)
                ]
                # Sort with natural key
                image_files.sort(key=alphanumeric_key)

                st.write("**Image Files (sorted):**", image_files)

                if not image_files:
                    st.warning("No valid image files found in the ZIP.")
                    return

                # Read the images into a list
                images_list = []
                for image_file in image_files:
                    with zip_ref.open(image_file) as file:
                        img_data = file.read()
                    img = Image.open(io.BytesIO(img_data))
                    # Convert RGBA/P modes to RGB
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    images_list.append(img)

                # ----- 2x2 Collage Creation -----
                # Chunk images into groups of 4
                def chunker(seq, size):
                    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

                collage_pages = []
                for group_of_four in chunker(images_list, 4):
                    # Find the max width and height among these up-to-4 images
                    max_width = max(img.width for img in group_of_four)
                    max_height = max(img.height for img in group_of_four)

                    # Create a blank "page" large enough for 2x2
                    collage_width = 2 * max_width
                    collage_height = 2 * max_height
                    collage = Image.new("RGB", (collage_width, collage_height), "white")

                    # Paste each image into the collage
                    for i, img in enumerate(group_of_four):
                        # Row and column in the 2x2 grid
                        row = i // 2  # 0 or 1
                        col = i % 2   # 0 or 1
                        x_offset = col * max_width
                        y_offset = row * max_height
                        collage.paste(img, (x_offset, y_offset))

                    # Append this collage "page" to the list
                    collage_pages.append(collage)

                # ----- Create the PDF -----
                pdf_buffer = io.BytesIO()
                # Pillow's "save_all" for multi-page PDF
                # The first image "collage_pages[0]" is used as the base, append the rest
                if collage_pages:
                    collage_pages[0].save(
                        pdf_buffer,
                        format="PDF",
                        save_all=True,
                        append_images=collage_pages[1:]
                    )
                    pdf_buffer.seek(0)

                    st.success("4-images-per-page PDF created!")
                    st.download_button(
                        label="Download PDF",
                        data=pdf_buffer,
                        file_name="4_per_page.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No collage pages were created.")

        except zipfile.BadZipFile:
            st.error("The uploaded file is not a valid ZIP archive.")

if __name__ == "__main__":
    main()
