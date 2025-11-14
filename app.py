import streamlit as st
import numpy as np
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os 
import requests
from bs4 import BeautifulSoup

#seeting up the cleint 
load_dotenv()
client = genai.Client(api_key=os.getenv("GAPI"))


st.set_page_config(page_icon='🎇', 
                   page_title='AgentSocial',
                   layout="wide")
st.title("AgentSocial")
st.caption('Your social media posting assistant')

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


def show_card(title, content):
    st.markdown(
        f"""
        <div style="
            background: #6673ff;
            padding: 18px 22px;
            border-radius: 12px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            margin-top: 10px;
        ">
            <p style="margin: 0 0 px">{title}</p>
            <p style="font-size: 1px; line-height: 1.5;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


#sidebar to uplaod the image
st.sidebar.header("Upload your social media post.")
uploaded= st.sidebar.file_uploader("Upload Image", type=['jpeg', 'png', 'jpg'])

leftcol, rightcol = st.columns(2)


#image understadning --- passing the image or the creative/graphic design 
with leftcol:
    if uploaded:
        st.image(uploaded, use_container_width =True)
        image_bytes = uploaded.getvalue()
     
        image_part = types.Part.from_bytes(
            data=image_bytes, 
            mime_type=uploaded.type  
        )
     
        if st.button("Review My Creative"):
            with st.spinner("Analyzing your graphic design"):
                try:
                    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        """You are an expert graphic desinger. Check the given creative/graphic design give it scores based on your understand in the following format:
                        - Color theme: /5
                        - Visual Appeal: /5
                        - Copy/Content: /5
                        - Clarity & impact: /5

                        Requirements:
                        1. Do not give any starter message like "Here is the summary..."
                        2. Keep the review short, to the point, max 2 lines.
                        3. Display the scores after the review and score best of your knowledge. 

                        """,
                        image_part,
                    ],
                )

                    st.caption("Genric review for your design:")
                    st.write(response.text)

                except Exception as e:
                    st.error(f"Error: {e}") 


with rightcol:
    #caption generation
    st.subheader("Generate Caption")

    tone = st.selectbox(
        "Select Tone",
        ["Professional", "Friendly", "Funny", "Minimal"]
    )

    style = st.selectbox(
        "Select Style",
        ["Short punchline", "Long storytelling", "Sales-focused", "Direct CTA"]
    )

    cta = st.text_input("Call-to-action (optional, e.g., 'DM us to order')")

    if st.button("Generate Caption"):

        prompt = f"""
            You are an expert social media copywriter.

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
        with st.spinner("hold on tight, generating the best caption..."):

            cap = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image_part]
            )
        show_card("Your caption:", cap.text)
        st.session_state["caption"]=cap.text




    st.markdown("---")
    st.subheader("Generate Hashtags")

    if "caption" not in st.session_state:
        st.info("Generate a caption first to enable hashtag generation.")
    else:

        # --- OPTIONS ---
        niche = st.selectbox(
            "Select Niche",
            [
                "General", "Fashion", "Food", "Fitness", "Real Estate",
                "Beauty", "Travel", "Tech", "Education", "Photography"
            ]
        )

        region = st.selectbox(
            "Target Region",
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

            You have a Caption:
            "{caption}"

            Niche: {niche}

            Region Trending Hashtags of the day:
            {trending_tags}

            TASK:
            - Generate a final list of 15–25 Instagram hashtags.
            - Blend the caption context + niche + trending tags.
            - Keep atleast 5-6 hashtags as it is from the {trending_tags} list 
            - Avoid spammy tags 
            - Avoid duplicates.
            - Keep them relevant and optimized for organic reach.
            - If region trending hashtags are provided, include 3–5 of the best ones.
            - Output ONLY the hashtags in a single clean list.

            Final Output Format:
            #tag1 #tag2 #tag3 ...
            """

            with st.spinner("Generating the most trendy Hashtags..."):

                tags = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt]
                )

            
            st.code(tags.text, language="markdown")
