# main.py

# --- Imports ---
import requests
import streamlit as st
import os
import time
import json
from streamlit_sortables import sort_items
import streamlit.components.v1 as components
# --- NEW: Import themes from the separate file ---
from themes import THEMES

# --- Configuration ---
DESIGN_URL = os.environ.get("DESIGN_SERVICE_URL", "https://design-generation-service-799115974158.asia-south1.run.app")
ANALYSIS_URL = os.environ.get("ANALYSIS_SERVICE_URL", "https://prompt-analysis-service-799115974158.asia-south1.run.app")
CONTENT_URL = os.environ.get("CONTENT_SERVICE_URL", "https://content-generation-service-799115974158.asia-south1.run.app")

# --- REMOVED: The large THEMES list is now in themes.py ---

# --- Function to load external CSS ---
def load_css(file_name):
    """Loads a CSS file and injects it into the Streamlit app."""
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- Apply Custom Styling from external file ---
load_css("style.css")

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
            try:
                error_detail = http_err.response.json().get("detail", http_err.response.text)
            except json.JSONDecodeError:
                error_detail = http_err.response.text
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
        num_slides = col1.slider("Number of slides", min_value=3, max_value=10, value=5)
        
        languages = [
            "English (US)", "English (UK)", "Hindi", "Bengali", "Assamese", "Marathi", "Tamil", "Telugu", "Gujarati",
            "Spanish", "French", "German", "Japanese", "Chinese (Simplified)", "Portuguese (Brazil)"
        ]
        language = col2.selectbox("Language", languages)
        
        submitted = st.form_submit_button("Generate Content Outline")
    if submitted and topic:
        with st.spinner("Analyzing your request..."):
            try:
                analysis_res = requests.post(f"{ANALYSIS_URL}/analyze", json={"prompt": topic}, timeout=45)
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

    for i, slide in enumerate(st.session_state.slide_data):
        slide_content = slide.get('data', {})
        
        with st.expander(f"Editing Slide {i+1}: {slide_content.get('title', 'Untitled')}", expanded=True):
            
            new_title = st.text_input(
                "Title", 
                value=slide_content.get('title', ''), 
                key=f"title_{i}"
            )
            st.session_state.slide_data[i]['data']['title'] = new_title

            if 'subtitle' in slide_content:
                new_subtitle = st.text_input(
                    "Subtitle", 
                    value=slide_content.get('subtitle', ''), 
                    key=f"subtitle_{i}"
                )
                st.session_state.slide_data[i]['data']['subtitle'] = new_subtitle

            points_key = 'points' if 'points' in slide_content else 'items'
            current_points = slide_content.get(points_key, [])
            
            points_as_text = "\n".join(current_points)
            
            new_points_text = st.text_area(
                "Content (one bullet point per line)",
                value=points_as_text,
                key=f"points_{i}",
                height=150
            )
            
            st.session_state.slide_data[i]['data'][points_key] = [
                line.strip() for line in new_points_text.split('\n') if line.strip()
            ]

    st.markdown("---")
    
    if st.button("Confirm Changes & Proceed to Finalize", type="primary", use_container_width=True):
        st.session_state.stage = 'generating'
        st.rerun()

# STAGE 4: Finalizing
elif st.session_state.stage == 'finalizing':
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