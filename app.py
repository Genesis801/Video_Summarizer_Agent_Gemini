import streamlit as st
from google import genai
from duckduckgo_search import DDGS
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import os

# -------------------------
# Load API key
# -------------------------

load_dotenv()
API_KEY = os.getenv("Gemini_API_Key")

client = genai.Client(api_key=API_KEY)

# -------------------------
# Streamlit UI
# -------------------------

st.title("🎥 YouTube Video Research Agent")

youtube_url = st.text_input("Enter YouTube URL")


# -------------------------
# Extract Video ID
# -------------------------
# example: https://www.youtube.com/shorts/C2vqQJ5Enpk
def get_video_id(url):

    parsed = urlparse(url)

    # youtu.be format
    if parsed.hostname in ["youtu.be"]:
        return parsed.path[1:]

    # youtube.com/watch?v=
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        query = parse_qs(parsed.query)

        if "v" in query:
            return query["v"][0]

        # shorts format
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]

        # embed format
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]

    return None

# -------------------------
# Get Transcript
# -------------------------

def get_transcript(video_id):

    api = YouTubeTranscriptApi()

    transcript = api.fetch(video_id)

    transcript = transcript[:1000]  # limit to first 100 segments for performance

    text = " ".join([i.text for i in transcript])

    return text


# -------------------------
# Web Search
# -------------------------

def search_web(query):

    context = []

    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)

        for r in results:
            context.append(r["body"])

    return "\n".join(context)


# -------------------------
# Gemini Summarization
# -------------------------
@st.cache_data
def summarize(transcript, web_context):

    prompt = f"""
    VIDEO TRANSCRIPT:
    {transcript[:1000]}

    WEB CONTEXT:
    {web_context}

    Tasks:
    1. Summarize the video
    2. Extract key ideas
    3. Add useful context from the web
    4. Provide insights
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


# -------------------------
# Run
# -------------------------

if youtube_url:

    with st.spinner("Analyzing video..."):

        print("Extracting video ID...")
        video_id = get_video_id(youtube_url)

        print("Fetching transcript...")
        transcript = get_transcript(video_id)

        print("Searching web for context...")
        web_context = search_web(youtube_url)

        print("Generating summary...")
        # summary = transcript
        summary = summarize(transcript, web_context)

    st.markdown(summary)