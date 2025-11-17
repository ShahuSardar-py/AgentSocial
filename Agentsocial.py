import streamlit as st
import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup

# Setup
load_dotenv()
client = genai.Client(api_key=os.getenv("GAPI"))

# ----------- GLOBAL UI STYLE -------------
st.set_page_config(page_icon='🎇', page_title='AgentSocial', layout="wide")

custom_css = """
<style>

/* GLOBAL THEME */
body, .stApp {
    background-color: #ffffff !important;
    font-family: 'Inter', sans-serif;
}

/* HEADERS */
h1, h2, h3, h4 {
    color: #1a1a1a !important;
}

/* CARD COMPONENT */
.card {
    background-color: #ffffff;
    padding: 18px 22px;
    border-radius: 14px;
    border: 1px solid #e8e8e8;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-top: 12px;
}

/* BUTTONS */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 500;
}

/* SIDEBAR CLEANUP */
.sidebar-content {
    padding: 8px;
    margin-top: 10px;
}

/* EXPANDERS */
.streamlit-expanderHeader {
    font-size: 15px !important;
    font-weight: 600 !important;
}

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ----------------------------------------

st.title("AgentSocial")
st.caption('Your social media posting assistant')

# ----------- FUNCTIONS -----------
def card(title, content):
    st.markdown(
        f"""
        <div class="card">
            <h4 style="margin-bottom: 8px; font-size:18px;">{title}</h4>
            <div style="font-size:15px; line-height:1.6;">{content}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_trending_hashtags(region="in"):
    url = f"https://www.tagsfinder.com/en-{region}/instagram/"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("Scraping error:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    hashtag_elements = soup.select("span.tag")

    hashtags = [tag.get_text(strip=True) for tag in hashtag_elements if tag.get_text().startswith("#")]
    return hashtags[:30]


# ----------- SIDEBAR -----------
st.sidebar.header("Upload your social media creative")

uploaded = st.sidebar.file_uploader("Upload Image", type=['jpeg', 'png', 'jpg'])

with st.sidebar.expander("Best Creative Practices"):
    st.markdown("""
- Use **4:5 aspect ratio** for Instagram  
- Stick to **2–4 colors**  
- Use **high contrast** for text  
- Allow **breathing space**  
- Highlight **one main message**  
- Use **clean fonts**  
- Avoid too much text  
- Export in **1080×1350px**  
    """)

# LAYOUT 
leftcol, rightcol = st.columns([1, 1])


# LEFT COLUMN — IMAGE + REVIEW
with leftcol:
    if uploaded:
        st.image(uploaded, use_container_width=True)
        image_bytes = uploaded.getvalue()

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=uploaded.type
        )

        if st.button("Review My Creative"):
            with st.spinner("Analyzing your graphic design..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            """
                            You are an expert graphic desinger. Check the given creative/graphic design give it scores based on your understand in the following format:
                            - Color theme: /5
                            - Visual Appeal: /5
                            - Copy/Content: /5
                            - Clarity & impact: /5

                            Requirements:
                            1. Keep the review short, max 2 lines.
                            2. Display the scores clearly.
                            """,
                            image_part,
                        ],
                    )

                    card("Creative Review", response.text)

                except Exception as e:
                    st.error(f"Error: {e}")



# RIGHT COLUMN — CAPTION + HASHTAGS GEN. 
with rightcol:
    st.subheader("Generate Caption")

    tone = st.selectbox("Select Tone", ["Professional", "Friendly", "Funny", "Minimal"])
    style = st.selectbox("Select Style", ["Short punchline", "Long storytelling", "Sales-focused", "Direct CTA"])
    langauge= st.selectbox("Select Language", ["English", "Hindi", "Marathi"])

    if st.button("Generate Caption"):
        prompt = f"""
            You are an expert social media copywriter.
            Create a caption for the image. 
            Tone: {tone}
            Style: {style}
            Langauge: {langauge or 'None'}

            Requirements:
            - Human-like, engaging caption
            - No hashtags 
            - Make sure its gramatically correct. 
            - No words like 'image' or 'analysis'
        """

        with st.spinner("Crafting a perfect caption..."):
            cap = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image_part]
            )

        st.session_state["caption"] = cap.text
        card("Your Caption", cap.text)

    st.markdown("---")
    st.subheader("Generate Hashtags")

    if "caption" not in st.session_state:
        st.info("Generate a caption first.")
    else:
        with st.expander("Your saved caption"):
            st.write(cap.text)
        niche = st.selectbox(
            "Select Niche",
            ["General", "Fashion", "Food", "Fitness", "Real Estate", "Beauty", "Travel", "Tech", "Education", "Photography"]
        )

        region = st.selectbox("Target Region", ["None", "India", "USA", "UK", "Australia"])

        if st.button("Generate Hashtags"):
            caption = st.session_state["caption"]

            trending_tags = []
            if region != "None":
                region_code = {"India": "in", "USA": "us", "UK": "gb", "Australia": "au"}.get(region, "in")
                trending_tags = get_trending_hashtags(region_code)

            prompt = f"""
            Caption: "{caption}"
            Niche: {niche}
            Trending: {trending_tags}

            Generate 15–25 hashtags.
            Include 4–6 trending regional tags.
            Output ONLY hashtags.
            """

            with st.spinner("Fetching the best hashtags..."):
                tags = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt]
                )

            card("Your Hashtags", tags.text)


# ----------- FOOTER -----------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.metric("🔗 Built by", "Eternity AI")

