import streamlit as st
import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup

# LangChain imports - simplified version
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# Setup
load_dotenv()
client = genai.Client(api_key=os.getenv("GAPI"))

# ----------- GLOBAL UI STYLE -------------
st.set_page_config(page_icon='🎇', page_title='AgentSocial', layout="wide")

custom_css = """
<style>
body, .stApp {
    background-color: #ffffff !important;
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, h4 {
    color: #1a1a1a !important;
}

.card {
    background-color: #ffffff;
    padding: 18px 22px;
    border-radius: 14px;
    border: 1px solid #e8e8e8;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-top: 12px;
}

.stButton > button {
    width: 100%;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 500;
}

.streamlit-expanderHeader {
    font-size: 15px !important;
    font-weight: 600 !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ----------------------------------------

st.title("🤖 AgentSocial")
st.caption('AI-Powered Social Media Assistant with LangChain')

# ----------- HELPER FUNCTIONS -----------
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
    """Fetch trending hashtags from the web"""
    url = f"https://www.tagsfinder.com/en-{region}/instagram/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    hashtag_elements = soup.select("span.tag")
    hashtags = [tag.get_text(strip=True) for tag in hashtag_elements if tag.get_text().startswith("#")]
    return hashtags[:30]


def analyze_creative(image_bytes, mime_type):
    """Analyze creative design using Gemini"""
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                """
                You are an expert graphic designer. Analyze the creative/graphic design and provide scores:
                - Color theme: /5
                - Visual Appeal: /5
                - Copy/Content: /5
                - Clarity & impact: /5
                
                Keep the review short, max 2 lines per aspect. Be specific and actionable.
                """,
                image_part,
            ],
        )
        return response.text
    except Exception as e:
        return f"Error analyzing creative: {e}"


def generate_caption_with_image(image_bytes, mime_type, tone, style, language):
    """Generate caption with image context using Gemini"""
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    
    prompt = f"""
    You are an expert social media copywriter.
    Create a caption for the image.
    Tone: {tone}
    Style: {style}
    Language: {language}
    
    Requirements:
    - Human-like, engaging caption
    - No hashtags
    - Grammatically correct
    - No words like 'image' or 'analysis'
    - Match the visual content perfectly
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt, image_part]
        )
        return response.text
    except Exception as e:
        return f"Error generating caption: {e}"


# ----------- LANGCHAIN CHAINS -----------
@st.cache_resource
def get_langchain_llm():
    """Initialize LangChain LLM"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GAPI"),
        temperature=0.7
    )


def create_hashtag_chain(llm):
    """Create LangChain chain for hashtag generation"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert social media hashtag specialist. 
        Generate relevant, engaging hashtags that will maximize reach and engagement.
        Consider trending hashtags, niche-specific tags, and general popular tags.
        Output ONLY hashtags, space-separated or one per line."""),
        ("human", """Caption: {caption}
Niche: {niche}
Region: {region}
Trending tags in this region: {trending_tags}

Generate 15-25 highly relevant hashtags. Include 4-6 trending tags if they fit the content.""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain


def create_strategy_chain(llm):
    """Create LangChain chain for social media strategy advice"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are AgentSocial, an expert social media strategist. 
        Provide actionable, specific advice for social media marketing.
        Be concise but comprehensive. Focus on practical tips."""),
        ("human", "{question}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain


def create_caption_optimizer_chain(llm):
    """Create LangChain chain for caption optimization"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a social media copywriting expert.
        Analyze and improve captions for maximum engagement.
        Consider hooks, call-to-actions, storytelling, and emotional appeal."""),
        ("human", """Original Caption: {caption}
Tone: {tone}
Platform: Instagram

Provide:
1. Brief analysis (2-3 sentences)
2. Improved version
3. Key improvements made""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain


# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "caption" not in st.session_state:
    st.session_state.caption = ""

# Initialize LangChain LLM
llm = get_langchain_llm()

# ----------- SIDEBAR -----------
st.sidebar.header("📤 Upload Creative")
uploaded = st.sidebar.file_uploader("Upload Image", type=['jpeg', 'png', 'jpg'])

with st.sidebar.expander("📋 Best Creative Practices"):
    st.markdown("""
- Use **4:5 aspect ratio** for Instagram
- Stick to **2-4 colors**
- Use **high contrast** for text
- Allow **breathing space**
- Highlight **one main message**
- Use **clean fonts**
- Avoid too much text
- Export in **1080×1350px**
    """)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: This app uses LangChain chains to intelligently process your content with AI!")

# LAYOUT
leftcol, rightcol = st.columns([1, 1])

# LEFT COLUMN — IMAGE + REVIEW
with leftcol:
    if uploaded:
        st.image(uploaded, use_container_width=True)
        image_bytes = uploaded.getvalue()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎨 Review Creative"):
                with st.spinner("AI analyzing design..."):
                    result = analyze_creative(image_bytes, uploaded.type)
                    card("Creative Review", result)
        
        with col2:
            if st.button("✨ Optimize Caption") and st.session_state.caption:
                with st.spinner("Optimizing with LangChain..."):
                    chain = create_caption_optimizer_chain(llm)
                    try:
                        optimized = chain.invoke({
                            "caption": st.session_state.caption,
                            "tone": "Engaging"
                        })
                        card("Caption Optimization", optimized)
                    except Exception as e:
                        st.error(f"Error: {e}")

# RIGHT COLUMN — CAPTION + HASHTAGS
with rightcol:
    st.subheader("✍️ Generate Caption")
    
    tone = st.selectbox("Tone", ["Professional", "Friendly", "Funny", "Minimal"])
    style = st.selectbox("Style", ["Short punchline", "Long storytelling", "Sales-focused", "Direct CTA"])
    language = st.selectbox("Language", ["English", "Hindi", "Marathi"])
    
    if st.button("Generate Caption") and uploaded:
        with st.spinner("Crafting perfect caption..."):
            caption = generate_caption_with_image(
                image_bytes, uploaded.type, tone, style, language
            )
            st.session_state.caption = caption
            card("Your Caption", caption)
    
    st.markdown("---")
    st.subheader("🏷️ Generate Hashtags")
    
    if not st.session_state.caption:
        st.info("💡 Generate a caption first to create relevant hashtags.")
    else:
        with st.expander("📝 Your saved caption"):
            st.write(st.session_state.caption)
        
        niche = st.selectbox(
            "Niche",
            ["General", "Fashion", "Food", "Fitness", "Real Estate", 
             "Beauty", "Travel", "Tech", "Education", "Photography"]
        )
        
        region = st.selectbox("Region", ["India", "USA", "UK", "Australia"])
        
        if st.button("🚀 Generate Hashtags with LangChain"):
            region_map = {"India": "in", "USA": "us", "UK": "gb", "Australia": "au"}
            region_code = region_map.get(region, "in")
            
            with st.spinner("LangChain analyzing and generating hashtags..."):
                try:
                    # Fetch trending hashtags
                    trending = get_trending_hashtags(region_code)
                    trending_str = ", ".join(trending[:10]) if trending else "No trending data"
                    
                    # Use LangChain chain for generation
                    hashtag_chain = create_hashtag_chain(llm)
                    
                    result = hashtag_chain.invoke({
                        "caption": st.session_state.caption,
                        "niche": niche,
                        "region": region,
                        "trending_tags": trending_str
                    })
                    
                    card("Your Hashtags", result)
                    
                    # Show trending tags used
                    if trending:
                        with st.expander("📊 Trending tags in this region"):
                            st.write(" ".join(trending[:15]))
                    
                except Exception as e:
                    st.error(f"Error: {e}")


