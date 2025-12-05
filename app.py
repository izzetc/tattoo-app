import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import base64

# Page Configuration
st.set_page_config(
    page_title="JustArt AI Tattoo Generator",
    page_icon="🎨",
    layout="centered"
)

# --- PASTE YOUR API KEY HERE ---
API_KEY = "AIzaSyD2BN8tmMSYnOIHBYJrOJnBNXDF2OnjPVI"

# --- HELPER FUNCTIONS ---

def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}" style="text-decoration: none;"><button style="background-color: #333333; border: 1px solid #555; color: white; padding: 10px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 14px; margin: 4px 2px; cursor: pointer; border-radius: 4px;">📥 {text}</button></a>'
    return href

def generate_tattoo_stencil(user_prompt, style):
    client = genai.Client(api_key=API_KEY)
    
    # Prompt Engineering for specific styles
    base_prompt = f"Tattoo design concept: {user_prompt}."
    
    if style == "Fine Line":
        style_prompt = "Style: Minimalist fine line tattoo, clean single needle work, delicate details, black ink only, no shading, white background."
    elif style == "Dotwork":
        style_prompt = "Style: Dotwork shading tattoo, stippling texture, geometric patterns, blackwork, high contrast, white background."
    elif style == "Engraving":
        style_prompt = "Style: Vintage engraving illustration, cross-hatching shading, linocut print look, black ink, detailed linework."
    elif style == "Sketch":
        style_prompt = "Style: Pencil sketch tattoo design, rough lines, hand-drawn look, black and grey, artistic, white paper background."
    elif style == "Realism (Black & Grey)":
        style_prompt = "Style: Hyper-realistic black and grey tattoo, soft shading, depth, 8k resolution, professional tattoo art."
    else: # Default Blackwork
        style_prompt = "Style: Bold blackwork tattoo, solid black areas, clean outlines, high contrast, traditional feel, white background."

    # Final Instruction for AI (Force Stencil/Clean Look)
    final_prompt = f"{base_prompt} {style_prompt} Output must be a clean, black and white tattoo design on a plain white background. High contrast, professional tattoo flash."

    try:
        # Generate with Imagen 4.0
        response = client.models.generate_images(
            model="imagen-4.0-generate-001", 
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            img = Image.open(BytesIO(image_bytes))
            return img, None
        else:
            return None, "The AI returned an empty response. Please try again."
            
    except Exception as e:
        return None, str(e)

# --- UI DESIGN (FRONTEND) ---

# Header Section
col1, col2 = st.columns([1, 5])
with col1:
    # You can change this icon to your own logo URL
    st.image("https://cdn-icons-png.flaticon.com/512/2913/2913482.png", width=60) 
with col2:
    st.title("AI Tattoo Stencil Generator")
    st.caption("Create unique tattoo designs in seconds. Powered by JustArtTattoo.")

st.markdown("---")

# Input Section
st.subheader("1. Describe Your Idea")
user_input = st.text_area(
    "What should the tattoo look like?", 
    height=100, 
    placeholder="Example: A geometric wolf howling at the moon, surrounded by roses, fine line style..."
)

st.subheader("2. Choose a Style")
selected_style = st.radio(
    "Select the artistic technique:",
    ("Fine Line", "Dotwork", "Engraving", "Realism (Black & Grey)", "Sketch", "Blackwork"),
    horizontal=True
)

st.markdown("---")

# Generate Button
if st.button("✨ Generate Design ✨", type="primary", use_container_width=True):
    if not user_input:
        st.warning("Please describe your tattoo idea first.")
    else:
        with st.spinner('AI is crafting your design... (This usually takes 10-15 seconds)'):
            
            generated_image, error_message = generate_tattoo_stencil(user_input, selected_style)
            
            if generated_image:
                st.success("Design generated successfully!")
                
                # Display Result
                st.image(generated_image, caption=f"Result: {selected_style} Style", use_column_width=True)
                
                # Download Button
                st.markdown(get_image_download_link(generated_image, "tattoo_design.png", "Download Design (PNG)"), unsafe_allow_html=True)
                st.info("💡 Tip: You can show this design to your tattoo artist for the final stencil.")
                
            else:
                st.error(f"An error occurred: {error_message}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 12px;'>"
    "Generated by JustArtTattoo AI Engine | © 2025 All Rights Reserved"
    "</div>", 
    unsafe_allow_html=True
)
