
import streamlit as st
import pandas as pd
import asyncio 

import nest_asyncio
from langdetect import detect, DetectorFactory,detect_langs

from googletrans import Translator
import os
from transformers import pipeline
import json



nest_asyncio.apply()
#emotion_classifier = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")
translator = Translator()

# Ensure consistent language detection
DetectorFactory.seed = 0


if "counter" not in st.session_state:
    st.session_state.counter = 0
    

# Load the languages from the config file
def load_languages():
    with open('config.json', 'r', encoding='utf-8') as file:
        languages = json.load(file)
    return languages

languages = load_languages()    
    
# Get the system username (works on both Linux & Windows)
username = os.getenv("USERNAME") or os.getenv("USER") or "Guest"

# Display greeting
st.write(f"Hello, **{username}**! Welcome to Streamlit. 🚀")

st.title("Text Processing & Language Detection")

# Step 1: Select input method
input_method = st.radio("Select input method:", ("Manual Text", "Upload CSV", "Use Example"))

text_data = ""

if input_method == "Manual Text":
    text_data = st.text_area("Enter text:", "")

elif input_method == "Upload CSV":
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if not df.empty:
            text_data = "\n".join(df.iloc[:, 0].dropna().astype(str))  # Assuming text is in the first column

elif input_method == "Use Example":
    text_data = """This is an example text.
    Voici un texte d'exemple.
    Dies ist ein Beispieltext.
    Esto es un texto de ejemplo."""
    
    st.write("Sample Data:", text_data)
 
if st.button("Start Processing"):
    st.session_state.counter += 1



# Step 2: Processing button
if st.session_state.counter > 0:
    if text_data:
        sentences = [s.strip() for s in text_data.split("\n") if s.strip()]
        
        # Create DataFrame with detected language
        data = []
        for sentence in sentences:
            try:
                detected_languages = detect_langs(sentence)
            except:
                detected_languages = "unknown"
            data.append({"Sentence": sentence, "Detected Language": detected_languages[0].lang,"Probability": detected_languages[0].prob, "Override": ""})

        df_lang = pd.DataFrame(data)

        # Store data in session state
        st.session_state["processed_data"] = df_lang

        # Display editable table
        st.session_state["edited_df"] = st.data_editor(df_lang, key="editable_table", num_rows="dynamic",disabled= ["Sentence","Detected Language","Probability"] )
        
        # Step 4: Validate Override Column
        invalid_rows = st.session_state["edited_df"] [~st.session_state["edited_df"] ["Override"].isin(languages) & st.session_state["edited_df"] ["Override"].ne("")]
    
        if not invalid_rows.empty:
            st.error("Invalid language code detected in 'Override' column. Please use valid ISO 639-1 codes.")

    else:
        st.warning("Please provide some text to process.")

    # Step 3: Commit Data Button (always visible)
    if text_data and  invalid_rows.empty:
        if "processed_data" in st.session_state and st.button("Commit Data"):
            edited_df = st.session_state["edited_df"]
           
            
            edited_df["Final Language"] = edited_df.apply(
                lambda row: row["Detected Language"] if row["Override"]==''  else row["Override"], axis=1
                )  
            edited_df = edited_df.drop(columns=["Override", "Detected Language","Probability"], errors="ignore")
            st.write("Committed Data (Final Version):", edited_df)
            
            
            async def translate_text(text, src_lang, dest_lang="en"):
                translation = await translator.translate(text, src=src_lang, dest=dest_lang)
                return translation.text
            
            async def translate_dataframe(df):
                df["Translated_Sentence"] = await asyncio.gather(*[translate_text(str(row["Sentence"]), row["Final Language"], "en") for _, row in df.iterrows()])
            
            async def run_async_task(task):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return await task  # ✅ Works inside Streamlit
                else:
                    return asyncio.run(task)  # ✅ Works in normal Python
               
            # # Check if event loop is running (Fix for Streamlit)
            # loop = asyncio.get_event_loop()
            # if loop.is_running():
            #     task = loop.create_task(translate_dataframe(edited_df))
            #     await task  # ✅ Works inside Streamlit
            # else:
            #     asyncio.run(translate_dataframe(edited_df))  # ✅ Works in normal Python scripts
            
            async def run_translate():
                await translate_dataframe(edited_df)  # Ensure translation is done before proceeding
                
            asyncio.run(run_translate()) 
          

          
            # def detect_emotion(text):
            #     result = emotion_classifier(text)
            #     return result[0]['label'],result[0]['score']  # Return the detected emotion label


            # edited_df[["Detected_Emotion", "Emotion_Score"]] = edited_df["Translated_Sentence"].astype(str).apply(detect_emotion).apply(pd.Series)
            st.write("Result:", edited_df)
            
            st.download_button(
                label="Download CSV",
                data=edited_df.to_csv(index=False),
                file_name="processed_data.csv",
                mime="text/csv"
            )   
if st.button("Reset App"):
    st.session_state.clear()  # Clears all stored session data
    st.rerun()  # Restarts the app
    
    
    
    
    

    
    