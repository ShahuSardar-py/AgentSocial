import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os


load_dotenv()
client = genai.Client(api_key=os.getenv("GAPI"))

st.set_page_config(page_icon='🎇', 
                   page_title='Creative agent',
                    layout="wide")

st.header("Creative agent")
st.caption("Generate viral hooks scripts")
st.divider()

with st.form("script_gen", clear_on_submit=False):
    st.header("Enter script details")
    #st.text_input("Platform")
    platform= st.selectbox("Choose Platform",
                           ["Instagram reel", 
                            "Youtube Short", 
                            "Introductory pitch"])
    col1,col2= st.columns(2)
    with col1:
         textt= st.text_area("enter")
         topic= textt
    with col2:
         brochure= st.file_uploader(
              "Uplaod Brochure",
              type=["pdf", "png", "jpg", "jpeg"]
         )
    tone= st.pills("Tone",["Casual",
                           "Energetic", 
                           "Emotional", 
                           "Premium" ,
                           "Minimal", 
                           "Bold" , 
                           "Storytelling", 
                           "Sarcastic/Gen-Z", 
                           "Fun"])
    
    hook_type= st.selectbox("Select ideal hook",
    ["Shock value", 
     "Question hook", 
     "Relatable problem",
     "Bold claim"])
    
  
    
    submitted= st.form_submit_button("Submit")

if submitted:
        prompt = f"""
            You are an expert script writer from a premium media house. You have been hired to write scripts for the users media production
            Create a strong script for {platform} video while keeping in mind the follwing personalizations user has decided upon:
            product details/topic: {topic or 'None'}
            tone: {tone or 'None'}
            hook = {hook_type}
            brochure= {brochure}
            If brochure content is provided, ignore the {topic} input entirely and treat the extracted brochure text as the only source of truth. Only create the script from the brochure content.

            Requirements:
            - Human-like, engaging script
            - make a professional format for this script. 
            - aviod too much cliches 
            - avoid heavy wording unless necessary
            - Do NOT add any introductions, explanations, or phrases like:
                "Sure, here's your script", "Absolutely", "Here you go", 
                "This is a punchy script", or any conversational filler.

            - Start the script DIRECTLY with the first line of the actual script.
            - Do NOT greet the user.

        """

        with st.spinner("Crafting a perfect caption..."):
            script = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )

        st.session_state["script"] = script.text
        st.write("Script", script.text)


# ----------- FOOTER -----------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.metric("🔗 Built by", "Eternity AI")
