import streamlit as st
import numpy as np
import streamlit as st
from google import genai
from google import genai
from dotenv import load_dotenv
import os 
from google.genai import types
import requests
from bs4 import BeautifulSoup

load_dotenv()
client = genai.Client(api_key=os.getenv("GAPI"))

st.set_page_config(page_icon='🎇', page_title='AgentSocial')

st.title("Gemini Image Understanding Demo")


#understadn image
uploaded= st.file_uploader("Upload Image", type=['jpeg', 'png', 'jpg'])
if uploaded:
     st.image(uploaded, use_column_width=True)
     image_bytes = uploaded.getvalue()
     
     image_part = types.Part.from_bytes(
        data=image_bytes, 
        mime_type=uploaded.type  # preserves correct mimetype
    )
     if st.button("Analyze Image"):
        with st.spinner("Calling Gemini..."):

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        "Understand the image/graphic design & give a sumnmary about it. explain what the design is trying to mention to the end-user",
                        image_part,
                    ],
                )

                st.subheader("Gemini Response:")
                st.write(response.text)

            except Exception as e:
                st.error(f"Error: {e}") 

st.markdown("---")
#caption gen
st.subheader("Generate Caption")

tone = st.selectbox(
    "Select Caption Tone",
    ["Professional", "Friendly", "Funny", "Luxurious", "Minimal"]
    )

style = st.selectbox(
    "Select Caption Style",
    ["Short punchline", "Long storytelling", "Sales-focused", "Informative"]
    )

cta = st.text_input("Call-to-action (optional, e.g., 'DM us to order')")

if st.button("Generate Caption"):

    prompt = f"""
        You are an expert social media caption writer.

        Create a caption for the image provided. 
        You must analyze the image *yourself* and understand the theme, emotion, product, or message.

        Tone: {tone}
        Style: {style}

        Personalization:
        Call-to-action: {cta or 'None'}

        Requirements:
        - Caption should be natural, engaging and feel human.
        - Avoid hashtags; they will be generated separately.
        - Do not mention 'image', 'picture', or describe the analysis process.
        - Do not repeat prompt details.
        - Keep it platform-ready for Instagram/Facebook.
        """
    with st.spinner("Writing caption..."):

        cap = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image_part]
        )

        st.subheader("Generated Caption")
        st.success(cap.text)
        st.session_state["caption"]=cap.text
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

    hashtags = []
    for tag in hashtag_elements:
        text = tag.get_text(strip=True)
        if text.startswith("#"):
            hashtags.append(text)

    return hashtags[:30]
st.markdown("---")
st.subheader("Generate Hashtags")

if "caption" not in st.session_state:
    st.info("Generate a caption first to enable hashtag generation.")
else:
    st.write("Caption:")
    st.success(st.session_state["caption"])

    # --- OPTIONS ---
    niche = st.selectbox(
        "Select Niche",
        [
            "General", "Fashion", "Food", "Fitness", "Real Estate",
            "Beauty", "Travel", "Tech", "Education", "Photography"
        ]
    )

    region = st.selectbox(
        "Target Region (optional)",
        ["None", "India", "USA", "UK", "Australia"]
    )

    if st.button("Generate Hashtags"):
        caption = st.session_state["caption"]

        # --- SCRAPE REGION TAGS ---
        trending_tags = []
        if region != "None":
            region_code = "in" if region == "India" else \
                          "us" if region == "USA" else \
                          "gb" if region == "UK" else \
                          "au" if region == "Australia" else "in"
            trending_tags = get_trending_hashtags(region_code)

        # --- LLM PROMPT ---
        prompt = f"""
        You are an expert social media strategist.

        Caption:
        "{caption}"

        Niche: {niche}

        Region Trending Hashtags:
        {trending_tags}

        TASK:
        - Generate a final list of 15–25 Instagram hashtags.
        - Blend the caption context + niche + trending tags.
        - Avoid spammy tags (#love, #instagood unless actually relevant).
        - Avoid duplicates.
        - Avoid extremely generic or banned tags.
        - Keep them relevant and optimized for organic reach.
        - If region trending hashtags are provided, include 3–5 of the best ones.
        - Output ONLY the hashtags in a single clean list.

        Final Output Format:
        #tag1 #tag2 #tag3 ...
        """

        with st.spinner("Generating Hashtags..."):

            tags = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )

            st.subheader("Generated Hashtags")
            st.code(tags.text, language="markdown")
