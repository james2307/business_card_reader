import streamlit as st
from PIL import Image
import pandas as pd
from utils.vision_parser import extract_card_info
from streamlit_cropper import st_cropper
import io
import json
import hmac

# 1. Page configuration
st.set_page_config(
    page_title="Business Card Scanner",
    page_icon="📇",
    layout="wide"
)

# 2. Helper functions
def safe_get_value(item):
    """Safely extract value from either a string or a dictionary"""
    if isinstance(item, dict):
        return next(iter(item.values()), "Not found")
    return item if item else "Not found"


def display_card_info(info, idx):
    """Display extracted information for a single card"""
    st.markdown(f"---\n### Business Card {idx + 1}")

    # Create columns for image and data
    img_col, data_col = st.columns([1, 2])

    with img_col:
        # Display image with edit button
        st.image(
            info.get('display_image', info['original_image']), 
            caption=f"Business Card {idx + 1}",
            use_container_width=True
        )
        st.button(
            f"✏️ Edit Image Display #{idx + 1}", 
            key=f"edit_btn_{idx}",
            on_click=toggle_edit_mode,
            args=(idx,)
        )

    with data_col:
        # Company Information
        st.markdown("#### 🏢 Company Information")
        cols = st.columns(3)

        with cols[0]:
            st.markdown("**Company Name**")
            st.write(info.get('company_name') or "Not found")

            st.markdown("**Company Phone**")
            phones = info.get('company_phone', [])
            for phone in phones:
                st.write(safe_get_value(phone))

        with cols[1]:
            st.markdown("**Company Email**")
            emails = info.get('company_email', [])
            for email in emails:
                st.write(safe_get_value(email))

            st.markdown("**Company Website**")
            websites = info.get('company_website', [])
            for website in websites:
                st.write(safe_get_value(website))

        with cols[2]:
            st.markdown("**Additional Details**")
            details = info.get('company_details_if_any', [])
            for detail in details:
                st.write(safe_get_value(detail))

        # Contact Person Information
        st.markdown("#### 👤 Contact Person(s)")
        contact_persons = info.get('contact_person', [])
        for i, person in enumerate(contact_persons):
            cols = st.columns(2)
            with cols[0]:
                st.write(f"**Name:** {person.get('name') or 'Not found'}")
                st.write(f"**Position:** {person.get('position') or 'Not found'}")
            with cols[1]:
                phones = person.get('personal_phone', [])
                emails = person.get('personal_email', [])
                if phones:
                    st.write("**Phone(s):** " + ", ".join([safe_get_value(p) for p in phones]))
                if emails:
                    st.write("**Email(s):** " + ", ".join([safe_get_value(e) for e in emails]))

        # Address Information
        st.markdown("#### 📍 Address")
        addresses = info.get('company_address', [])
        for addr in addresses:
            cols = st.columns(5)
            cols[0].write(f"**Street:** {addr.get('remaining') or 'Not found'}")
            cols[1].write(f"**City:** {addr.get('city') or 'Not found'}")
            cols[2].write(f"**State:** {addr.get('state') or 'Not found'}")
            cols[3].write(f"**Country:** {addr.get('country') or 'Not found'}")
            cols[4].write(f"**Pincode:** {addr.get('pincode') or 'Not found'}")

def toggle_edit_mode(idx):
    """Toggle edit mode for an image"""
    if st.session_state.editing_image == idx:
        st.session_state.editing_image = None
    else:
        st.session_state.editing_image = idx

def save_edited_image(idx, img):
    """Save edited image and clear edit mode"""
    st.session_state.processed_cards[idx]['display_image'] = img
    st.session_state.editing_image = None
    st.rerun()

def clear_all():
    """Clear all session state and refresh page"""
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Force page refresh
    st.experimental_rerun()


    # Display all processed cards
    for idx, info in enumerate(st.session_state.processed_cards):
        display_card_info(info, idx)

    # Clear results button - simplified
    if st.button("Clear All Results"):
        clear_all()
# 3. Initialize session state
# After page config, initialize all session states
if 'processed_cards' not in st.session_state:
    st.session_state.processed_cards = []
if 'editing_image' not in st.session_state:
    st.session_state.editing_image = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = None

# 4. Password protection
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# 5. Main UI and logic
# Title and description
st.title("📇 Business Card Scanner")
st.markdown("""
Upload one or multiple business card images to extract contact information automatically.
Supported formats: PNG, JPG, JPEG
""")


# Handle image editing if active
if st.session_state.editing_image is not None:
    idx = st.session_state.editing_image
    if idx < len(st.session_state.processed_cards):
        st.markdown("### 🖼️ Edit Image Display")
        card = st.session_state.processed_cards[idx]
        img = card['original_image']

        # Create columns for edit controls
        edit_cols = st.columns([3, 1])

        # Image cropping
        with edit_cols[0]:
            cropped_img = st_cropper(
                img,
                realtime_update=True,
                box_color='#2196F3',
                aspect_ratio=None,
                return_type='image'
            )

        # Controls
        with edit_cols[1]:
            # Rotation control
            rotation = st.selectbox(
                "Rotate",
                [0, 90, 180, 270],
                key=f"rotate_{idx}"
            )
            if rotation:
                cropped_img = cropped_img.rotate(rotation, expand=True)

            # Save/Cancel buttons
            if st.button("✅ Save Changes", key=f"save_edit_{idx}"):
                save_edited_image(idx, cropped_img)

            if st.button("❌ Cancel", key=f"cancel_edit_{idx}"):
                st.session_state.editing_image = None
                st.rerun()

# File uploader
uploaded_files = st.file_uploader(
    "Choose business card image(s)",
    type=['png', 'jpg', 'jpeg'],
    accept_multiple_files=True,
    help="Upload one or more business card images",
    key="file_uploader"  # Add key for tracking
)

if uploaded_files:
    # Track successful and failed cards
    failed_cards = []
    
    try:
        progress_text = "Processing business cards..."
        total_files = len(uploaded_files)
        progress_bar = st.progress(0, text=progress_text)

        # Process each file
        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                # Update progress
                progress = (idx + 1) / total_files
                progress_bar.progress(progress, text=f"Processing card {idx + 1} of {total_files}...")

                # Read and store the image
                image = Image.open(uploaded_file)

                # Extract information
                info = extract_card_info(image)
                info['filename'] = uploaded_file.name
                info['original_image'] = image
                st.session_state.processed_cards.append(info)
                
            except Exception as e:
                failed_cards.append({
                    'filename': uploaded_file.name,
                    'error': str(e)
                })
                continue  # Skip to next card

        # Complete progress bar
        progress_bar.progress(1.0, text="Processing complete!")

        # Show error summary if any
        if failed_cards:
            st.error(f"Failed to process {len(failed_cards)} cards:")
            for card in failed_cards:
                st.warning(f"- {card['filename']}: {card['error']}")

        # Show export options immediately after processing
        if st.session_state.processed_cards:
            st.subheader("💾 Export Options")

            # Convert to DataFrame for export
            export_data = []
            for card in st.session_state.processed_cards:
                # Create a copy without the image to avoid CSV export issues
                card_data = card.copy()
                card_data.pop('original_image', None)
                card_data.pop('display_image', None)
                export_data.append(card_data)

            df = pd.DataFrame(export_data)

            # CSV export button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="business_cards.csv",
                mime="text/csv",
                help="Download all extracted information as CSV"
            )

    except Exception as e:
        st.error(f"An error occurred while processing the image: {str(e)}")
        st.write("Please try uploading a different image or ensure the image is clear and well-lit.")

# Always display processed cards if they exist
if st.session_state.processed_cards:
    # Display all processed cards
    for idx, info in enumerate(st.session_state.processed_cards):
        display_card_info(info, idx)

    # Clear results button
    if st.button("Clear All Results"):
        clear_all()  # This will clear everything and refresh

# Add footer
st.markdown("""
---
Made with ❤️
""")
