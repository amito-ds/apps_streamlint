import os
import re
import streamlit as st
import zipfile
from PIL import Image
import io


def alphanumeric_key(filename):
    """
    Convert filename into a list of string and integer chunks for "natural" sorting.
    E.g. "10.png" -> ['','10',''] + ['.png'] -> [ '', 10, '' , '.png' ].
    """
    base, ext = os.path.splitext(filename)
    # split by digits, keeping the digits in the result
    parts = re.split(r'(\d+)', base)
    # convert numeric strings to integers, everything else to lowercase
    return [int(p) if p.isdigit() else p.lower() for p in parts] + [ext.lower()]


def main():
    st.title("Combine Images in ZIP to a Single PDF")

    uploaded_zip = st.file_uploader("Upload a ZIP containing images", type=["zip"])
    if uploaded_zip is not None:
        try:
            with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff")

                # Raw list from ZIP
                all_files = zip_ref.namelist()
                st.write("**Files in ZIP (unsorted):**", all_files)

                # Keep only valid image files
                image_files = [
                    f for f in all_files
                    if f.lower().endswith(valid_extensions)
                ]
                # Sort with natural key
                image_files.sort(key=alphanumeric_key)

                # Show the *sorted* list
                st.write("**Image Files (sorted):**", image_files)

                if not image_files:
                    st.warning("No valid image files found in the ZIP.")
                    return

                images_list = []
                for image_file in image_files:
                    # Read into memory
                    with zip_ref.open(image_file) as file:
                        image_data = file.read()
                    img = Image.open(io.BytesIO(image_data))
                    # Convert if needed
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    images_list.append(img)

                # Combine into PDF
                pdf_buffer = io.BytesIO()
                images_list[0].save(
                    pdf_buffer,
                    format="PDF",
                    save_all=True,
                    append_images=images_list[1:]
                )
                pdf_buffer.seek(0)

                st.success("Images successfully combined into PDF!")
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="combined.pdf",
                    mime="application/pdf"
                )
        except zipfile.BadZipFile:
            st.error("The uploaded file is not a valid ZIP archive.")


if __name__ == "__main__":
    main()
