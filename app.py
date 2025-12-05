import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import base64
import time
from supabase import create_client, Client

# --- GİZLİ BİLGİLER (ST.SECRETS'DEN GELECEK) ---
# Artık şifreleri buraya yazmıyoruz, sunucudan çekeceğiz.
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("Şifreler bulunamadı! Lütfen Streamlit Secrets ayarlarını yapın.")
    st.stop()
# --- AYARLAR ---
st.set_page_config(page_title="Fallink Studio", page_icon="✨", layout="centered", initial_sidebar_state="collapsed")

# --- VERİTABANI BAĞLANTISI ---
@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Supabase connection error: {e}")
        return None

supabase = init_connection()

# --- YARDIMCI FONKSİYONLAR ---

def check_user_credits(username):
    """Kullanıcı kredisini kontrol eder."""
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            return user_data["credits"]
        else:
            return -1 # Kullanıcı yok
    except Exception as e:
        st.error(f"Database error: {e}")
        return -1

def deduct_credit(username, current_credits):
    """Kullanıcıdan 1 kredi düşer."""
    try:
        new_credit = current_credits - 1
        supabase.table("users").update({"credits": new_credit}).eq("username", username).execute()
        return new_credit
    except Exception as e:
        st.error(f"Credit deduction error: {e}")
        return current_credits

def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}" class="download-btn">📥 {text}</a>'
    return href

def generate_tattoo_stencil(user_prompt, style, placement):
    try:
        # Client'ı başlatıyoruz
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        base_prompt = f"Tattoo design concept: {user_prompt}. Placement: {placement}."
        
        styles = {
            "Fine Line Minimalist": "Style: Ultra-thin fine line tattoo, single needle, minimalist, clean, delicate, black ink only, no shading, negative space.",
            "Micro Realism": "Style: Micro realism tattoo, incredible detail in small scale, fine black and grey shading, photographic quality.",
            "Dotwork & Geometry": "Style: Dotwork shading, sacred geometry patterns, mandalas, stippling, precise dots, blackwork.",
            "Engraving / Woodcut": "Style: Vintage engraving illustration, cross-hatching, linocut print texture, old book illustration feel.",
            "Sketch": "Style: Pencil sketch, rough guidelines, artistic, unfinished look, charcoal texture on paper.",
            "Blackwork": "Style: Bold blackwork, solid blackfill areas, heavy lines, high contrast, tribal or ornamental patterns."
        }
        style_prompt = styles.get(style, styles["Blackwork"])
        final_prompt = f"{base_prompt} {style_prompt} Output must be a clean, high-contrast tattoo design on a plain white background."

        # --- GÜNCELLEME BURADA: SENİN HESABINDAKİ 4.0 MODELİNİ SEÇTİK ---
        response = client.models.generate_images(
            model="imagen-4.0-generate-001", 
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            img = Image.open(BytesIO(image_bytes))
            return img, None
        return None, "AI returned empty response."
    except Exception as e:
        return None, str(e)

# --- CSS (TASARIM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'SF Pro Display', sans-serif; color: #1d1d1f; }
    .stButton > button { background-color: #000000 !important; color: white !important; border-radius: 8px !important; border: none !important; }
    .stButton > button:hover { background-color: #333333 !important; }
    .credit-badge { background-color: #f5f5f7; padding: 5px 15px; border-radius: 20px; font-weight: 600; font-size: 14px; color: #000; border: 1px solid #e1e1e1; }
</style>
""", unsafe_allow_html=True)

# --- UYGULAMA AKIŞI ---

if "logged_in_user" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>Fallink Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: grey;'>AI Tattoo Generator</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username_input = st.text_input("Access Code", placeholder="e.g. admin")
        if st.button("Login", use_container_width=True):
            credits = check_user_credits(username_input)
            if credits == -1:
                st.error("Invalid access code!")
            else:
                st.session_state["logged_in_user"] = username_input
                st.session_state["credits"] = credits
                st.success("Login successful!")
                time.sleep(1)
                st.rerun()
    st.stop()

# Giriş Sonrası Ekran
user = st.session_state["logged_in_user"]
credits = check_user_credits(user) 

col_a, col_b = st.columns([3,1])
with col_a:
    st.markdown(f"**Member:** {user}")
with col_b:
    st.markdown(f"<div class='credit-badge'>💎 {credits} Credits</div>", unsafe_allow_html=True)

st.markdown("---")

st.subheader("Create New Design")
user_prompt = st.text_area("Describe your tattoo idea", height=100, placeholder="E.g. A geometric lion roaring, minimal style...")

c1, c2 = st.columns(2)
with c1:
    style = st.selectbox("Select Style", ("Fine Line Minimalist", "Micro Realism", "Dotwork & Geometry", "Engraving / Woodcut", "Sketch", "Blackwork"))
with c2:
    placement = st.selectbox("Placement", ("Arm", "Leg", "Chest", "Back", "Wrist", "Neck"))

if st.button("Generate Design (1 Credit)", type="primary", use_container_width=True):
    if credits < 1:
        st.error("Not enough credits! Please top up.")
    elif not user_prompt:
        st.warning("Please describe your idea.")
    else:
        with st.spinner("AI is inking (using Imagen 4.0)..."):
            new_credits = deduct_credit(user, credits)
            st.session_state["credits"] = new_credits
            
            img, err = generate_tattoo_stencil(user_prompt, style, placement)
            
            if img:
                st.balloons()
                st.image(img, caption="Fallink AI Design", use_column_width=True)
                st.markdown(get_image_download_link(img, "fallink_design.png", "Download Image"), unsafe_allow_html=True)
                st.success(f"Design ready! Remaining credits: {new_credits}")
            else:
                st.error(f"Error: {err}")
