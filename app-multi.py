import streamlit as st
import torch
from torchvision import transforms, models
from PIL import Image
import os

from supabase import create_client, Client

st.set_page_config(page_title="DeepFake Detector: Buildings", page_icon="Light_Icon.png", layout="centered")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize Supabase client
SUPABASE_URL = "https://kwmpxpodmpwplujkpwjn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3bXB4cG9kbXB3cGx1amtwd2puIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxOTMzMzMwNywiZXhwIjoyMDM0OTA5MzA3fQ.ZZM2pFJeBi3Tl6xI1NNzv3f4ETs2iIcS1EqkIowuO-M"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define the path to the saved model
MODEL_PATH = "models/buildings_deepfake_detector_mobilenet_v3_small_ep_10.pth"

# Define the image size and transforms
image_size = (240, 240)
image_transforms = transforms.Compose([
    transforms.Resize(image_size),
    transforms.ToTensor(),
])

@st.cache_resource
def load_model():
    # Load the model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.mobilenet_v3_small(pretrained=False)
    num_features = model.classifier[3].in_features
    model.classifier[3] = torch.nn.Linear(num_features, 2)  # Adjust the final layer to match your classes
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model = model.to(device)
    model.eval()
    return model, device

model, device = load_model()

# Define class names
class_names = ["fake", "real"]

st.image("logo-banner2.png")

# App header
st.subheader("GaussMass 1.0")

st.markdown(
"""
- AI Detection Tool that uses in-house fundamental infrastructure
- 93% accuracy within seconds of reaction
- Help analyze files including photos and videos
- Safeguard against deepfake content
"""
)

# Initialize session state for email and feedback
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'predictions' not in st.session_state:
    st.session_state.predictions = []

# File uploader
uploaded_files = st.file_uploader("Choose images...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    st.session_state.predictions = []

    # Process each uploaded image
    for uploaded_file in uploaded_files:
        # Load the uploaded image
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption=f"Uploaded Image: {uploaded_file.name}", use_column_width=True)

        # Transform the image and prepare it for prediction
        image_tensor = image_transforms(image).unsqueeze(0).to(device)

        # Predict the class
        with torch.no_grad():
            outputs = model(image_tensor)
            _, predicted = torch.max(outputs, 1)
            prediction = class_names[predicted.item()]
            st.session_state.predictions.append((uploaded_file.name, prediction))

    # Email input
    st.session_state.email = st.text_input("Enter your email to see whether they're fake:", value=st.session_state.email)

    if st.session_state.email and st.button("Submit"):
        # Display the predictions
        for filename, prediction in st.session_state.predictions:
            st.write(f"Prediction for {filename}: This is **{prediction.capitalize()}**")

        # Thumbs up/down feedback
        feedback = st.radio("Was this prediction helpful?", ("", "Yes", "No"))
        if feedback:
            for filename, prediction in st.session_state.predictions:
                with open("feedback.txt", "a") as f:
                    f.write(f"Email: {st.session_state.email}, Filename: {filename}, Prediction: {prediction}, Feedback: {feedback}\n")
                response = supabase.table('UserFeedback').insert({
                    'email_id': st.session_state.email,
                    'filename': filename,
                    'prediction': prediction,
                    'feedback': feedback
                }).execute()

            if response:
                st.success("Thank you for your feedback!")
            else:
                st.error("There was an error submitting your feedback. Please try again.")

print('Search completed.')
