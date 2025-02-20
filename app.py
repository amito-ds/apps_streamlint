import os
import re
import streamlit as st
import zipfile
from PIL import Image
import io
import math

# ---------- Helper Functions ----------

def alphanumeric_key(filename):
    """
    Convert filename into a list of string and integer chunks for "natural" sorting.
    E.g. "10.png" -> ['','10',''] + ['.png'] -> [ '', 10, '' , '.png' ].
    """
    base, ext = os.path.splitext(filename)
    parts = re.split(r'(\d+)', base)
    return [int(p) if p.isdigit() else p.lower() for p in parts] + [ext.lower()]

def chunker(seq, size):
    """Yield successive chunks of length `size` from `seq`."""
    for pos in range(0, len(seq), size):
        yield seq[pos:pos + size]

# ---------- Main App Function ----------
def main():
    # ---- Page Config ----
    st.set_page_config(
        page_title="Combine Images to PDF",
        layout="centered",
        initial_sidebar_state="auto"
    )

    # ---- Custom CSS (for a cleaner look) ----
    st.markdown("""
        <style>
        /* Center the main title */
        .main-title {
            text-align: center; 
            color: #4B4B4B;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        /* Subtitle style */
        .sub-title {
            text-align: center;
            color: #6E6E6E;
        }
        /* Box around the file uploader */
        .stFileUploader label {
            font-weight: bold;
        }
        /* Improve the button styling */
        .css-5uatcg edgvbvh10 {
            border-radius: 6px;
        }
        /* Adjust the PDF download button */
        .stDownloadButton button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            margin-top: 15px;
        }
        /* Add some spacing under the expander/sections */
        .st-expander {
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---- Title and Instructions ----
    st.markdown("<h1 class='main-title'>Combine Images into a Single PDF</h1>", unsafe_allow_html=True)
    st.markdown("<h4 class='sub-title'>Upload a ZIP of images and choose how many images per page.</h4>", unsafe_allow_html=True)
    st.write("")

    # ---- Sidebar for Settings ----
    st.sidebar.title("Settings")
    images_per_page = st.sidebar.number_input(
        "Images per PDF page:",
        min_value=1,
        max_value=25,
        value=4,
        step=1
    )

    st.sidebar.write("""
    **Instructions:**
    1. Upload a ZIP file containing image files (JPG, PNG, etc.).
    2. Choose how many images should go on each PDF page.
    3. Click "Download PDF" once the processing is complete.
    """)

    # ---- File Uploader ----
    uploaded_zip = st.file_uploader("Upload a ZIP containing images", type=["zip"])
    if uploaded_zip is not None:
        try:
            with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff")

                # Raw list of files from ZIP
                all_files = zip_ref.namelist()

                # Keep only valid image files
                image_files = [
                    f for f in all_files
                    if f.lower().endswith(valid_extensions)
                ]

                # Sort with natural key
                image_files.sort(key=alphanumeric_key)

                # Visualization: Show file lists in an expander
                with st.expander("Preview: ZIP File Contents"):
                    st.write("**All Files (unsorted):**")
                    st.write(all_files)
                    st.write("**Valid Image Files (sorted):**")
                    st.write(image_files)

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

                # ----- Create Collage Pages -----
                collage_pages = []

                # For each group of "images_per_page"
                for group_of_n in chunker(images_list, images_per_page):
                    n_in_this_chunk = len(group_of_n)

                    # For this chunk, decide how many columns/rows in the grid
                    # We'll aim for a square-ish layout:
                    cols = int(math.ceil(math.sqrt(n_in_this_chunk)))
                    rows = int(math.ceil(n_in_this_chunk / cols))

                    # Determine the max width/height for images in this chunk
                    max_width = max(img.width for img in group_of_n)
                    max_height = max(img.height for img in group_of_n)

                    # Create a blank collage image
                    collage_width = cols * max_width
                    collage_height = rows * max_height
                    collage = Image.new("RGB", (collage_width, collage_height), "white")

                    # Paste each image into the collage grid
                    for i, img in enumerate(group_of_n):
                        row = i // cols
                        col = i % cols
                        x_offset = col * max_width
                        y_offset = row * max_height
                        collage.paste(img, (x_offset, y_offset))

                    collage_pages.append(collage)

                # ----- Create the PDF -----
                pdf_buffer = io.BytesIO()
                if collage_pages:
                    collage_pages[0].save(
                        pdf_buffer,
                        format="PDF",
                        save_all=True,
                        append_images=collage_pages[1:]
                    )
                    pdf_buffer.seek(0)

                    st.success(f"PDF created successfully with {images_per_page} image(s) per page!")
                    st.download_button(
                        label="Download PDF",
                        data=pdf_buffer,
                        file_name=f"{images_per_page}_per_page.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No collage pages were created.")

        except zipfile.BadZipFile:
            st.error("The uploaded file is not a valid ZIP archive.")

# ---------- Run the App ----------
if __name__ == "__main__":
    main()
