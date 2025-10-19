# --- Imports ---
import requests
import streamlit as st
import os
import time
import json
from streamlit_sortables import sort_items
import streamlit.components.v1 as components

# --- Configuration ---
DESIGN_URL = os.environ.get("DESIGN_SERVICE_URL", "https://design-generation-service-799115974158.asia-south1.run.app")
ANALYSIS_URL = os.environ.get("ANALYSIS_SERVICE_URL", "https://prompt-analysis-service-799115974158.asia-south1.run.app/analyze")
CONTENT_URL = os.environ.get("CONTENT_SERVICE_URL", "https://content-generation-service-799115974158.asia-south1.run.app")

# Data structure for themes
THEMES = [
    {
        "id": "minimalist",
        "name": "Minimalist",
        "desc": "Modern and clean",
        "colors": ["#4A4A4A", "#F0F0F0", "#6E6E6E", "#FBF30D"],
        "fonts": "Heading: Archivo Black, Body: Archivo Black",
        "image_ref": "image_4bde3c.png"
    },
    {
        "id": "mystique",
        "name": "Mystique",
        "desc": "Dark and sophisticated",
        "colors": ["#A855F7", "#6D28D9", "#374151", "#E5E7EB"],
        "fonts": "Heading: Blinker, Body: Merriweather Sans Light",
        "image_ref": "image_4bd396.png"
    },
    {
        "id": "streamline",
        "name": "Streamline",
        "desc": "Professional and bold",
        "colors": ["#3B82F6", "#1D4ED8", "#F9FAFB", "#4B5563"],
        "fonts": "Heading: Aptos (Headings), Body: Aptos Light (Body)",
        "image_ref": "placeholder"
    },
    {
        "id": "forest",
        "name": "Forest",
        "desc": "Natural and serene",
        "colors": ["#16A34A", "#15803D", "#F0FDF4", "#4ADE80"],
        "fonts": "Heading: Gluten, Body: Cambay",
        "image_ref": "placeholder"
    },
    {
        "id": "sunset",
        "name": "Sunset",
        "desc": "Warm and inviting",
        "colors": ["#F97316", "#EA580C", "#FFF7ED", "#FB923C"],
        "fonts": "Heading: DM Sans, Body: DM Sans",
        "image_ref": "placeholder"
    },
    {
        "id": "orbit",
        "name": "Orbit",
        "desc": "Futuristic and dynamic",
        "colors": ["#6366F1", "#4338CA", "#EEF2FF", "#A5B4FC"],
        "fonts": "Heading: Montserrat ExtraBold, Body: Poppins",
        "image_ref": "placeholder"
    }
]

# --- Custom Styling ---
st.markdown(""" 
<style>
    /* Gradient Background for the main page */
    .stApp {
        background: linear-gradient(to bottom, #000000, #2c2c2c); /* Black to dark gray gradient */
        background-attachment: fixed;
    }
    
    .stAlert[data-testid="stAlert"] { border-radius:10px; border:2px solid; padding:1rem; font-family:'Inter',sans-serif; }
    .stAlert[data-baseweb="alert"] > div:nth-child(2) { color:white; }
    .stAlert[data-baseweb="alert"][data-testid="stAlert"] { border-color:#2E7D32; background-color:#1E4620; }
    .stAlert[data-baseweb="alert"][data-testid="stAlert"].st-emotion-cache-1pxazr7 { border-color:#0288D1; background-color:#012A36; }
    
    /* General Button Style */
    .stButton>button, .stDownloadButton>button { 
        border-radius:10px; 
        padding:10px 20px; 
        font-weight:bold; 
    }

    /* --- ✅ FIX: Primary Button Style for ALL Primary Buttons --- */
    /* This targets both regular and download buttons with type="primary" */
    .stButton button[kind="primary"],
    .stDownloadButton button {
        background-color: #ff4a42; /* A strong, custom red */
        color: #FFFFFF !important; /* Ensures text is white and visible */
        border: none;
    }
    /* A slightly lighter red on hover for better user feedback */
    .stButton button[kind="primary"]:hover,
    .stDownloadButton button:hover {
        background-color: #fc6760;
        color: #FFFFFF !important;
        border: none;
    }


    .stAlert + .stAlert, .stButton { margin-top:20px !important; }
    div[data-testid="stVerticalBlock"] div[data-testid="stSortable"] div[data-baseweb="card"] { background-color:#2E2E2E !important; color:#FFFFFF !important; font-weight:bold !important; border-radius:8px; margin-bottom:8px !important; padding:12px 15px; border:1px solid #444444; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .st-emotion-cache-1wbqy5k { color:#FFFFFF; }
    .review-page-title, .review-page-info { margin-bottom:25px; }

    /* --- STYLES FOR THEME SELECTION --- */
    .theme-card {
        background-color: #1F2937;
        border: 2px solid #374151;
        border-radius: 10px;
        padding: 1.5rem;
        transition: all 0.2s ease-in-out;
        margin-bottom: 1rem;
    }
    .theme-card.selected {
        border-color: #60A5FA;
        box-shadow: 0 4px 12px rgba(96, 165, 250, 0.3);
    }
    .theme-card-header {
        font-size: 1.25rem;
        font-weight: bold;
        color: #F9FAFB;
    }
    .theme-card-desc {
        color: #D1D5DB;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        height: 40px;
    }
    .theme-preview-colors {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .theme-preview-color {
        width: 25px;
        height: 25px;
        border-radius: 50%;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .theme-preview-font {
        font-size: 0.8rem;
        color: #9CA3AF;
        margin-top: 1rem;
        height: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'input'
if 'slide_data' not in st.session_state:
    st.session_state.slide_data = []
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}
if 'final_presentation' not in st.session_state:
    st.session_state.final_presentation = {}
if 'selected_theme' not in st.session_state:
    st.session_state.selected_theme = THEMES[0]['id']


# --- UI Functions ---
def theme_picker():
    st.subheader("Select a Visual Theme")
    
    cols = st.columns(3)
    
    for i, theme in enumerate(THEMES):
        col = cols[i % 3]
        with col:
            card_class = "theme-card selected" if st.session_state.selected_theme == theme['id'] else "theme-card"
            
            st.markdown(f"""
                <div class="{card_class}">
                    <div class="theme-card-header">{theme['name']}</div>
                    <div class="theme-card-desc">{theme['desc']}</div>
                    <div class="theme-preview-colors">
                        {''.join([f'<div class="theme-preview-color" style="background-color:{color};"></div>' for color in theme['colors']])}
                    </div>
                    <div class="theme-preview-font">{theme['fonts']}</div>
                </div>
            """, unsafe_allow_html=True)

            if st.button(f"Select {theme['name']}", key=f"theme_{theme['id']}", use_container_width=True):
                st.session_state.selected_theme = theme['id']
                st.rerun()

def display_slide_content(slide):
    data = slide.get('data', {})
    st.markdown(f"### {data.get('title', 'Untitled Slide')}")
    if data.get('subtitle'):
        st.markdown(f"*{data.get('subtitle')}*")
    points = data.get('points', data.get('items', []))
    for point in points:
        st.markdown(f"- {point}")
    if data.get('message'):
        st.markdown(f"**{data.get('message')}**")

def stream_content_generation(analysis_data):
    try:
        response = requests.post(f"{CONTENT_URL}/generate-content", json=analysis_data, timeout=180)
        response.raise_for_status()
        full_content = response.json().get("slides", [])
        st.session_state.slide_data = full_content
        for slide in st.session_state.slide_data:
            with st.container(border=True):
                display_slide_content(slide)
        return True
    except Exception as e:
        st.error(f"Failed to generate content: {e}", icon="⚠️")
        return False

def generate_final_presentation():
    payload = {
        "slides": st.session_state.slide_data,
        "theme": st.session_state.selected_theme,
    }
    
    spinner_text = "Creating your presentation, adding your theme, inserting images, and getting everything set up. This may take a few moments..."
    with st.spinner(spinner_text):
        try:
            response = requests.post(f"{DESIGN_URL}/generate-full-presentation", json=payload, timeout=600)
            response.raise_for_status()
            st.session_state.final_presentation = response.json()
            return True
        except requests.exceptions.HTTPError as http_err:
            error_detail = http_err.response.json().get("detail", http_err.response.text)
            st.error(f"Failed to build presentation: {error_detail}", icon="⚠️")
            return False
        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to the presentation service: {e}", icon="⚠️")
            return False

# --- UI Rendering Stages ---

# STAGE 1: User Input
if st.session_state.stage == 'input':
    st.title("FinDeck AI: Your Finance PPT Assistant")
    with st.form("ppt_form_step1"):
        topic = st.text_area("Define your presentation's core thesis or topic.", "The impact of AI on investment banking.", height=100)
        col1, col2 = st.columns(2)
        num_slides = col1.slider("Number of slides", min_value=3, max_value=15, value=7)
        
        languages = [
            "English (US)", "English (UK)", "Hindi", "Bengali", "Assamese", "Marathi", "Tamil", "Telugu", "Gujarati",
            "Spanish", "French", "German", "Japanese", "Chinese (Simplified)", "Portuguese (Brazil)"
        ]
        language = col2.selectbox("Language", languages)
        
        submitted = st.form_submit_button("Generate Content Outline")
    if submitted and topic:
        with st.spinner("Analyzing your request..."):
            try:
                analysis_res = requests.post(ANALYSIS_URL, json={"prompt": topic}, timeout=45)
                analysis_res.raise_for_status()
                st.session_state.analysis_data = analysis_res.json()
                st.session_state.analysis_data['slide_count'] = num_slides
                st.session_state.analysis_data['language'] = language
                st.session_state.stage = 'generating'
                st.rerun()
            except Exception as e:
                st.error(f"Analysis Failed: {e}", icon="⚠️")

# STAGE 2: Content Generation and Theme Selection
elif st.session_state.stage == 'generating':
    st.header("Synthesizing Your Content Outline...")
    if not st.session_state.slide_data:
        generation_successful = stream_content_generation(st.session_state.analysis_data)
    else:
        for slide in st.session_state.slide_data:
            with st.container(border=True):
                display_slide_content(slide)
        generation_successful = True

    if generation_successful:
        st.success("Your content strategy has been drafted.")
        st.markdown("---")
        
        theme_picker()
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        if col1.button("Refine Content Manually", use_container_width=True):
            st.session_state.stage = 'review'
            st.rerun()
        
        if col2.button("Finalize & Build Presentation", type="primary", use_container_width=True):
            st.session_state.stage = 'finalizing'
            st.rerun()

# STAGE 3: Review and Edit Stage
elif st.session_state.stage == 'review':
    st.title("Refine Your Content Strategy")
    st.info("Review and edit the generated slide content below. Your changes are saved as you type.")

    # Iterate through each slide to make its content editable
    for i, slide in enumerate(st.session_state.slide_data):
        slide_content = slide.get('data', {})
        
        # We use an expander for each slide to keep the UI clean
        with st.expander(f"Editing Slide {i+1}: {slide_content.get('title', 'Untitled')}", expanded=True):
            
            # --- EDITABLE TITLE ---
            # The 'key' is crucial to make each widget unique
            new_title = st.text_input(
                "Title", 
                value=slide_content.get('title', ''), 
                key=f"title_{i}"
            )
            st.session_state.slide_data[i]['data']['title'] = new_title

            # --- EDITABLE SUBTITLE (if it exists) ---
            if 'subtitle' in slide_content:
                new_subtitle = st.text_input(
                    "Subtitle", 
                    value=slide_content.get('subtitle', ''), 
                    key=f"subtitle_{i}"
                )
                st.session_state.slide_data[i]['data']['subtitle'] = new_subtitle

            # --- EDITABLE BULLET POINTS ---
            # We handle both 'points' or 'items' as possible keys for bullet points
            points_key = 'points' if 'points' in slide_content else 'items'
            current_points = slide_content.get(points_key, [])
            
            # Join the list of points into a single string for the text_area
            points_as_text = "\n".join(current_points)
            
            new_points_text = st.text_area(
                "Content (one bullet point per line)",
                value=points_as_text,
                key=f"points_{i}",
                height=150
            )
            
            # Split the text from the text_area back into a list, removing empty lines
            st.session_state.slide_data[i]['data'][points_key] = [
                line.strip() for line in new_points_text.split('\n') if line.strip()
            ]

    st.markdown("---")
    
    # This button takes you back to the theme selection page with your updated content
    if st.button("Confirm Changes & Proceed to Finalize", type="primary", use_container_width=True):
        st.session_state.stage = 'generating'
        st.rerun()

# STAGE 4: Finalizing
elif st.session_state.stage == 'finalizing':
    # ✅ ROBUST FIX: This Javascript component uses a timeout and targets multiple
    # elements to ensure the scroll command works reliably after the page redraws.
    components.html(
        """
        <script>
            window.setTimeout(function() {
                window.location.href = "#top";
            }, 100);
        </script>
        """,
        height=0
    )
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)   
    st.header("Finalizing Your Presentation...")

    if generate_final_presentation():
        st.balloons()
        st.session_state.stage = 'complete'
        st.rerun()
    else:
        # This part only shows if the generation fails
        if st.button("Return to Editor"):
            st.session_state.stage = 'generating'
            st.rerun()

# STAGE 5: Complete
elif st.session_state.stage == 'complete':
    st.title("Your FinDeck Presentation is Complete!")
    final_data = st.session_state.final_presentation
    download_url = final_data.get("download_url")
    preview_url = final_data.get("preview_url")
    if preview_url:
        st.subheader("Presentation Preview")
        st.components.v1.iframe(preview_url, height=500, scrolling=True)
        st.markdown("---")
    if download_url:
        try:
            ppt_content = requests.get(download_url, timeout=60).content
            st.download_button(
                label="Download Presentation (.pptx)",
                data=ppt_content, 
                file_name="FinDeck_Presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.error(f"Could not fetch the presentation file. Please use this direct link: {download_url}")
            st.markdown(f"**[Download Link]({download_url})**")
    
    if st.button("Start Again!"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

