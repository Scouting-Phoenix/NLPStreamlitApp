import streamlit as st
import pandas as pd
from langdetect import detect, DetectorFactory

# Ensure consistent language detection
DetectorFactory.seed = 0

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

# Step 2: Processing button
if st.button("Start Processing"):
    if text_data:
        sentences = [s.strip() for s in text_data.split("\n") if s.strip()]
        
        # Create DataFrame with detected language
        data = []
        for sentence in sentences:
            try:
                detected_lang = detect(sentence)
            except:
                detected_lang = "unknown"
            data.append({"Sentence": sentence, "Detected Language": detected_lang, "Override": ""})

        df_lang = pd.DataFrame(data)

        # Display editable table
        edited_df = st.data_editor(df_lang, key="editable_table", num_rows="dynamic")

        # Show final result
        st.write("Processed Data:", edited_df)
    else:
        st.warning("Please provide some text to process.")