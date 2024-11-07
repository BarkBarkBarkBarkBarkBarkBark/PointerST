import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import numpy as np
import tempfile
import os
import openai

# Initialize OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define the WebRTC client settings
WEBRTC_CLIENT_SETTINGS = ClientSettings(
#    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"}]},
#    media_stream_constraints={"audio": True, "video": False},
#
    rtc_configuration={
        "iceServers": [
            {
                "urls": ["stun:stun.l.google.com:19302"]
            }
        ]
    }
)

st.title("Verbal Chat with Whisper and GPT-4")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to process audio frames
def process_audio_frames(frames):
    audio_data = b''.join(frames)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        tmpfile.write(audio_data)
        audio_path = tmpfile.name
    return audio_path

# Start the WebRTC streamer
webrtc_ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDRECV,
    client_settings=WEBRTC_CLIENT_SETTINGS,
    audio_receiver_size=256,
    async_processing=True,
)

if webrtc_ctx.state.playing:
    if "audio_frames" not in st.session_state:
        st.session_state.audio_frames = []

    status_indicator = st.empty()
    record_button = st.button("Start Recording")
    stop_button = st.button("Stop Recording and Transcribe")

    if record_button:
        status_indicator.info("Recording... Speak now!")
        st.session_state.audio_frames = []

    if webrtc_ctx.audio_receiver and st.session_state.audio_frames is not None:
        try:
            audio_frame = webrtc_ctx.audio_receiver.get_frame(timeout=1)
            st.session_state.audio_frames.append(audio_frame.to_ndarray().tobytes())
        except:
            pass

    if stop_button and st.session_state.audio_frames:
        status_indicator.info("Processing audio...")
        audio_path = process_audio_frames(st.session_state.audio_frames)
        status_indicator.info("Transcribing audio...")
        # Transcribe using Whisper API
        transcript = transcribe_audio(audio_path)
        st.write(f"**You said:** {transcript}")

        # Generate response using OpenAI
        with st.spinner("Generating response..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": transcript}
                ]
            )
            assistant_message = response['choices'][0]['message']['content']
            st.write(f"**Assistant:** {assistant_message}")

        # Clean up temporary file
        os.remove(audio_path)

        # Update conversation history
        st.session_state.messages.append({"role": "user", "content": transcript})
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})

        # Display conversation history
        for msg in st.session_state.messages:
            st.write(f"**{msg['role'].capitalize()}:** {msg['content']}")

        # Reset audio frames
        st.session_state.audio_frames = []

else:
    st.warning("Please allow access to your microphone.")

# Optional Text Input
st.write("Or type your question below:")
user_input = st.text_input("Your question")

if user_input:
    with st.spinner("Generating response..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": user_input}
            ]
        )
        assistant_message = response['choices'][0]['message']['content']
        st.write(f"**Assistant:** {assistant_message}")

    # Update conversation history
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})

    # Display conversation history
    for msg in st.session_state.messages:
        st.write(f"**{msg['role'].capitalize()}:** {msg['content']}")

# Function to transcribe audio using Whisper API
def transcribe_audio(file_path):
    """Transcribes audio using OpenAI's Whisper API."""
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript['text']
