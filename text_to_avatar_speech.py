import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

# Streamlit app setup
st.set_page_config(page_title="Text to Avatar Speech", page_icon="🗣️")
st.title("Text to Avatar Speech")

# Language code to full name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French", 
    "ja": "Japanese",
    "ko": "Korean"
}

# Hardcoded password (not secure for production use)
PASSWORD = "chatbot"

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Authentication logic
if not st.session_state.authenticated:
    password_input = st.text_input("Enter Password:", type="password")
    if password_input == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()  # Prevents the rest of the page from loading

# Main app content (only shown if authenticated)
st.write("Welcome! Enter text and select voice settings to generate avatar speech videos.")
st.write("The avatar will repeat exactly what you type using the selected voice.")

# Debug mode toggle in sidebar
st.sidebar.subheader("Advanced Settings")
debug_mode = st.sidebar.checkbox("Enable Debug Mode")

# API Keys
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
HEYGEN_API_URL = "https://api.heygen.com/v2"

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Talking photo options
talking_photo_options = {
    "d29ec865893443cb955b59075739db4d": {"display_name": "Eric"},
    "8347186cc9384a0a97ac194524fcc907": {"display_name": "于林臣"},
    "b582e62171694c949c7c3afc66685723": {"display_name": "冉牧泽"},
    "493a7b96f3964ac5904eea183f0dabe9": {"display_name": "刘小河"},
    "23fb4768add443f99b804f898be9fd44": {"display_name": "张驰之"},
    "d2697c13f66e4401a12293d52c751554": {"display_name": "苏木子"},
    "134096eeaaf54dd3891f4d490c000545": {"display_name": "王郁甄"},
    "2bd6da8785bd456c8d33837d3a639f70": {"display_name": "刘奕好"},
    "55ccabd216c84e5080e5941071533bc4": {"display_name": "刘泫熙"},
    "62221c9e9f084bc3b770b89097fcb8a5": {"display_name": "刘畅"},
    "cc417088f836488c97a9e1c44a1fd719": {"display_name": "刘轩铭"},
    "5b9a038f5bae4f6e8d51d058fe7aa4c1": {"display_name": "崔家瑜"},
    "d18ce50684ea46db813228d6e9c25ef7": {"display_name": "徐少辰"},
    "d269297004b9447b8deb764bbbf2a7db": {"display_name": "李墨涵"},
    "c0ae2bf400fd4291953675e69def9dbf": {"display_name": "杨子阅"},
    "e9495eb9b0f041c6b6aceb6e143ab9c1": {"display_name": "王子路"},
    "883c15dfb62242548464d9d6a81b4db5": {"display_name": "詹圣娇"},
    "ac3249b26be34735a0e336d7b833aaed": {"display_name": "黄俊杰"},
}

# Voice selection controls in sidebar
st.sidebar.title("Voice Settings")

# Language selection
selected_language = st.sidebar.selectbox(
    "Select Language",
    options=list(LANGUAGE_NAMES.keys()),
    format_func=lambda x: LANGUAGE_NAMES[x],
    index=0  # Default to English
)

# Gender selection
selected_gender = st.sidebar.radio(
    "Select Gender",
    options=["female", "male"],
    index=0,  # Default to female
    horizontal=True
)

# Age selection
selected_age = st.sidebar.radio(
    "Select Age",
    options=["young", "mature"],
    index=0,  # Default to young
    horizontal=True
)

# Talking photo selection
st.sidebar.subheader("Avatar Selection")
selected_character = st.sidebar.selectbox(
    "Choose Talking Photo", 
    options=list(talking_photo_options.keys()),
    format_func=lambda x: talking_photo_options[x]["display_name"]
)

# Display current voice selection
voice_category = f"{selected_gender}_{selected_age}"
st.sidebar.info(f"**Current Voice Selection:**\n- Language: {LANGUAGE_NAMES[selected_language]}\n- Type: {selected_gender.title()} {selected_age.title()}")

# Function to detect language of text with more detailed detection
def detect_language(text):
    # Check for Chinese characters
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return "zh"
    
    # Check for Japanese characters (Hiragana, Katakana)
    if any('\u3040' <= char <= '\u30ff' for char in text):
        return "ja"
    
    # Check for Korean characters
    if any('\uac00' <= char <= '\ud7a3' for char in text):
        return "ko"
    
    # Check for common Spanish words
    spanish_words = ["el", "la", "los", "las", "un", "una", "y", "o", "pero", "porque", "como", "qué", "cuándo", "dónde"]
    words = text.lower().split()
    if any(word in spanish_words for word in words) and any('á' in text or 'é' in text or 'í' in text or 'ó' in text or 'ú' in text or 'ñ' in text):
        return "es"
    
    # Check for common French words
    french_words = ["le", "la", "les", "un", "une", "des", "et", "ou", "mais", "parce", "que", "comment", "quand", "où"]
    if any(word in french_words for word in words) and any('é' in text or 'è' in text or 'ê' in text or 'ç' in text or 'à' in text):
        return "fr"
    
    # Default to English
    return "en"

def generate_heygen_video(character_id, text, selected_voice_id):
    # Create progress tracking elements
    progress_placeholder = st.empty()
    progress_bar = st.progress(0)
    progress_placeholder.info("Preparing to generate video...")
    
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": HEYGEN_API_KEY
    }
    
    # Voice ID mapping by language and gender
    voice_map = {
        # English voices
        "en": {
            "female_young": "1bd001e7e50f421d891986aad5158bc8",  # Daisy (young female)
            "female_mature": "2d5b0e6cf36f460aa7fc47e3eee4ba54",  # Alice (mature female)
            "male_young": "e95166076b8c458abcd636a5f59b0e81",    # Daniel (young male)
            "male_mature": "11a8b3b5ea33441294501cb8fc45f3da",   # Matthew (mature male)
        },
        # Chinese voices
        "zh": {
            "female_young": "00c8fd447ad7480ab1785825978a2215",  # Using correct voice ID for female_young
            "female_mature": "5b3f164f63ee46b5bcb28e21e7f5427e",  # Luli (mature female)
            "male_young": "7a72eedf88374b65a2a3f873bd471d73",    # Xiaotong (young male)
            "male_mature": "e1adcef3cf42401b84b0fa5ea8b14b77",   # Zhigang (mature male)
        },
        # Spanish voices
        "es": {
            "female_young": "41a37ffe4f3742cd94fc9f0263c7d697",  # Sofia (young female)
            "female_mature": "2fb39c2a1df94fbab396a85f72b5e48b",  # Isabella (mature female)
            "male_young": "2d2d443a7bbb4663942c19f3ad5b025d",    # Miguel (young male)
            "male_mature": "e3f58532df7d4df79c1c7176a7fb3cd1",   # Javier (mature male)
        },
        # Japanese voices
        "ja": {
            "female_young": "3984e56f97204e98b51d26bef43e2c8f",  # Aiko (young female)
            "female_mature": "21cad0c84c5543bba5fd4fb31abd0078",  # Yumi (mature female)
            "male_young": "a2ad6ae9c3b64b47ba2423cefba33c9a",    # Takashi (young male)
            "male_mature": "b08c4f76ceb54e3295337bb78f0dc0c4",   # Kenji (mature male)
        },
        # Korean voices
        "ko": {
            "female_young": "aea35fae3a4640dbb107e23c71260b99",  # Ji-woo (young female)
            "female_mature": "5f4d8a8e33a44b8c814cb0b6e2197a2d",  # Seo-yeon (mature female)
            "male_young": "9dd9a7c8c4e44c6d8f1282a0f93d1acf",    # Min-jun (young male)
            "male_mature": "faf3431b55cf4a268a5f6f62f4063764",   # Joon-ho (mature male)
        },
        # French voices
        "fr": {
            "female_young": "ab14736db6e24d07b49c4bd75bee21d2",  # Chloé (young female)
            "female_mature": "1e6a91f6ea764eba9fc56a209c71f169",  # Sophie (mature female)
            "male_young": "74dc44e4df9e40ee8c4bb241391b27bb",    # Lucas (young male)
            "male_mature": "9fae597cc45b4fc39056a583a2ac18d9",   # Pierre (mature male)
        }
    }
    
    progress_placeholder.info(f"Using voice ID: {selected_voice_id}")
    
    # Log the voice selection if debug mode is enabled
    if debug_mode:
        progress_placeholder.info(f"Debug Info: Voice ID: {selected_voice_id}")
    
    # Talking photo payload structure
    character_config = {
        "type": "talking_photo",
        "talking_photo_id": character_id
    }
    
    # Updated payload structure for v2 API
    payload = {
        "video_inputs": [
            {
                "character": character_config,
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": selected_voice_id
                },
                "background": {
                    "type": "color",
                    "value": "#ffffff"  # White background
                }
            }
        ],
        "dimension": {
            "width": 720,  # Lower resolution for free tier
            "height": 406   # 16:9 aspect ratio
        },
        "test": True,  # Enable test mode for the free tier
        "title": "Text to Avatar Speech"
    }
    
    # Debug logging if enabled
    if debug_mode:
        st.sidebar.subheader("API Request Debug")
        st.sidebar.code(json.dumps(payload, indent=2), language="json")
    
    try:
        # Try v2 API first
        progress_placeholder.info("Sending request to HeyGen API...")
        response = requests.post(f"{HEYGEN_API_URL}/video/generate", 
                                headers=headers, 
                                data=json.dumps(payload))
        
        # If v2 fails, try v1 endpoint
        if response.status_code != 200:
            progress_placeholder.info("Trying alternative API endpoint...")
            # Log the error if debug mode is enabled
            if debug_mode:
                try:
                    error_json = response.json()
                    st.sidebar.warning("V2 API Error Response:")
                    st.sidebar.code(json.dumps(error_json, indent=2), language="json")
                except:
                    st.sidebar.warning(f"V2 API Error: {response.text}")
            
            # Create v1 payload for talking photo
            v1_payload = {
                "talking_photo_id": character_id,
                "voice_type": "text",
                "voice_input": text,
                "voice_id": selected_voice_id,
                "background": "#ffffff",
                "test": True,
                "title": "Text to Avatar Speech"
            }
            
            # Log the v1 payload if debug mode is enabled
            if debug_mode:
                st.sidebar.info("Trying V1 API with payload:")
                st.sidebar.code(json.dumps(v1_payload, indent=2), language="json")
                
            # Make the v1 API call with proper headers and using json parameter
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Api-Key": HEYGEN_API_KEY
            }
            response = requests.post(
                "https://api.heygen.com/v1/video.task", 
                headers=headers, 
                json=v1_payload  # Use json parameter instead of data
            )
            
        if response.status_code != 200:
            # Handle error response properly
            error_message = "Unknown error"
            try:
                # Try to parse the error JSON
                error_json = response.json()
                if "error" in error_json and error_json["error"]:
                    if isinstance(error_json["error"], dict) and "message" in error_json["error"]:
                        error_message = f"Error: {error_json['error']['message']}"
                        if "detail" in error_json["error"]:
                            error_message += f" - {error_json['error']['detail']}"
                    else:
                        error_message = f"Error: {error_json['error']}"
                elif "message" in error_json:
                    error_message = f"Error: {error_json['message']}"
            except:
                # If we can't parse JSON, use the raw text
                error_message = f"Error creating video (HTTP {response.status_code}): {response.text}"
            
            st.error(error_message)
            if debug_mode:
                st.sidebar.error("API Error Details:")
                st.sidebar.code(response.text, language="json")
            return None
        
        # Handle different response formats between v1 and v2
        response_json = response.json()
        
        # v1 API returns data with task_id, v2 returns data with video_id
        if "task_id" in response_json.get("data", {}):
            video_id = response_json.get("data", {}).get("task_id")
        else:
            video_id = response_json.get("data", {}).get("video_id")
            
        if not video_id:
            st.error("Failed to get video ID")
            return None
            
        # Log the video ID for debugging
        progress_placeholder.info(f"Video ID: {video_id}")
        
        # Check video status and wait for completion
        status = "pending"
        attempt_count = 0
        max_attempts = 200  # Increased to 10 minutes (3 sec × 200)
        
        with st.spinner(""):
            while status in ["pending", "processing", "waiting"]:
                # Update progress info
                progress_percent = min(90, attempt_count * 0.45)  # Slower progress to reflect longer wait
                progress_bar.progress(int(progress_percent))
                progress_placeholder.info(f"Generating video: {progress_percent:.0f}% complete (this may take 5-10 minutes)")
                
                time.sleep(3)  # Check every 3 seconds
                attempt_count += 1
                
                # Modified status check for consistent endpoint handling
                try:
                    # First try v1 endpoint - most reliable for status checks
                    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
                    status_response = requests.get(status_url, headers=headers)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json().get("data", {})
                        status = status_data.get("status")
                        
                        # Show more detailed status info if debug mode is enabled
                        if debug_mode:
                            st.sidebar.info(f"Status check response:")
                            st.sidebar.code(json.dumps(status_response.json(), indent=2), language="json")
                        
                        progress_placeholder.info(f"Generating video: {progress_percent:.0f}% complete - Status: {status} (attempt {attempt_count}/{max_attempts})")
                        
                        if status == "completed":
                            video_url = status_data.get("video_url")
                            progress_bar.progress(100)
                            progress_placeholder.success("Video generation complete!")
                            return video_url
                        elif status == "failed":
                            error_details = status_data.get("error", {})
                            if isinstance(error_details, dict):
                                error_message = error_details.get("message", "Unknown error")
                                error_detail = error_details.get("detail", "")
                                error_code = error_details.get("code", "")
                                error_text = f"Video generation failed: {error_message}"
                                if error_detail:
                                    error_text += f". {error_detail}"
                                if error_code:
                                    error_text += f" (Code: {error_code})"
                            else:
                                error_text = f"Video generation failed: {error_details}"
                            
                            progress_placeholder.error(error_text)
                            if debug_mode:
                                st.sidebar.error("Error details:")
                                st.sidebar.code(json.dumps(error_details, indent=2), language="json")
                            return None
                    else:
                        # Try v2 endpoint as fallback
                        status_url = f"https://api.heygen.com/v2/video_status.get?video_id={video_id}"
                        status_response = requests.get(status_url, headers=headers)
                        
                        if status_response.status_code == 200:
                            try:
                                status_data = status_response.json().get("data", {})
                                status = status_data.get("status")
                                
                                if status == "completed":
                                    video_url = status_data.get("video_url")
                                    progress_bar.progress(100)
                                    progress_placeholder.success("Video generation complete!")
                                    return video_url
                                elif status == "failed":
                                    error_details = status_data.get("error", {})
                                    progress_placeholder.error(f"Video generation failed: {error_details}")
                                    return None
                            except Exception as parse_error:
                                progress_placeholder.warning(f"Could not parse V2 status response: {parse_error}")
                except Exception as e:
                    # If we can't connect, don't fail - just continue checking
                    progress_placeholder.info(f"Waiting for video processing... (attempt {attempt_count}/{max_attempts})")
            
            # Continue checking even if we reach max attempts
            if attempt_count >= max_attempts:
                progress_placeholder.info("Still waiting for video generation... (It can take up to 15 minutes)")
                
                # Check status again
                try:
                    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
                    status_response = requests.get(status_url, headers=headers)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json().get("data", {})
                        status = status_data.get("status")
                        
                        # If video is still processing, reset counter to keep checking
                        if status in ["pending", "processing", "waiting"]:
                            attempt_count = 0  # Reset counter to keep checking
                            max_attempts = 200  # Another 10 minutes
                        
                        # If completed, return the URL
                        if status == "completed":
                            video_url = status_data.get("video_url")
                            progress_bar.progress(100)
                            progress_placeholder.success("Video generation complete!")
                            return video_url
                except:
                    # If error, just log it
                    pass
                
                # If we still can't get the video
                progress_placeholder.warning("Video taking longer than expected.")
                return None
                    
        return None
    except Exception as e:
        st.error(f"Error with API: {e}")
        return None

# Chat interface
user_input = st.chat_input("Type your message here...")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            if "video_url" in message and message["video_url"]:
                st.video(message["video_url"])
            st.write(message["content"])

# Process new user input
if user_input:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display the user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Detect the language of user input
    detected_language = detect_language(user_input)
    
    # Check if detected language matches selected language
    if detected_language != selected_language:
        # Show warning and stop processing
        with st.chat_message("assistant"):
            warning_message = f"⚠️ Language mismatch detected!\n\nYour text appears to be in **{LANGUAGE_NAMES.get(detected_language, detected_language)}** but you have selected **{LANGUAGE_NAMES[selected_language]}** voice.\n\nPlease either:\n- Change your voice language to {LANGUAGE_NAMES.get(detected_language, detected_language)}, or\n- Rewrite your text in {LANGUAGE_NAMES[selected_language]}"
            st.warning(warning_message)
        
        # Store warning in session state
        st.session_state.messages.append({
            "role": "assistant", 
            "content": warning_message,
            "video_url": None
        })
    else:
        # Languages match, proceed with video generation
        # The response is just the user input (repeat what they said)
        response_text = user_input
        
        # Create assistant message container first
        assistant_container = st.chat_message("assistant")
        assistant_container.write(response_text)
        
        # Show video generation status
        video_status = assistant_container.empty()
        language_name = LANGUAGE_NAMES[selected_language]
        video_status.info(f"Generating avatar video in {language_name}... (please wait 5-10 minutes)")
        
        # Get the voice ID for the selected language, gender, and age
        voice_map = {
            "en": {
                "female_young": "1bd001e7e50f421d891986aad5158bc8",
                "female_mature": "2d5b0e6cf36f460aa7fc47e3eee4ba54",
                "male_young": "e95166076b8c458abcd636a5f59b0e81",
                "male_mature": "11a8b3b5ea33441294501cb8fc45f3da",
            },
            "zh": {
                "female_young": "00c8fd447ad7480ab1785825978a2215",
                "female_mature": "7c2e216ee89a488b9796f16067baa189",
                "male_young": "961546a1be64458caa1386ff63dd5d5f",
                "male_mature": "422dbf6b037648b69f663cd33b47007b",
            },
            "es": {
                "female_young": "41a37ffe4f3742cd94fc9f0263c7d697",
                "female_mature": "2fb39c2a1df94fbab396a85f72b5e48b",
                "male_young": "2d2d443a7bbb4663942c19f3ad5b025d",
                "male_mature": "e3f58532df7d4df79c1c7176a7fb3cd1",
            },
            "ja": {
                "female_young": "3984e56f97204e98b51d26bef43e2c8f",
                "female_mature": "21cad0c84c5543bba5fd4fb31abd0078",
                "male_young": "a2ad6ae9c3b64b47ba2423cefba33c9a",
                "male_mature": "b08c4f76ceb54e3295337bb78f0dc0c4",
            },
            "ko": {
                "female_young": "aea35fae3a4640dbb107e23c71260b99",
                "female_mature": "5f4d8a8e33a44b8c814cb0b6e2197a2d",
                "male_young": "9dd9a7c8c4e44c6d8f1282a0f93d1acf",
                "male_mature": "faf3431b55cf4a268a5f6f62f4063764",
            },
            "fr": {
                "female_young": "ab14736db6e24d07b49c4bd75bee21d2",
                "female_mature": "1e6a91f6ea764eba9fc56a209c71f169",
                "male_young": "74dc44e4df9e40ee8c4bb241391b27bb",
                "male_mature": "9fae597cc45b4fc39056a583a2ac18d9",
            }
        }
        
        # Get the voice ID based on user selection
        voice_id = voice_map[selected_language][voice_category]
        
        # Generate video with the user input using selected voice
        video_url = generate_heygen_video(
            selected_character,
            response_text,
            voice_id
        )
        
        # Update the response with the video
        if video_url:
            video_status.empty()
            assistant_container.video(video_url)
        else:
            # Show error message
            video_status.error(
                f"Video generation failed. Possible reasons: "
                f"1) The voice may not support the text. "
                f"2) API rate limit exceeded. "
                f"3) Service unavailable."
            )
        
        # Store in session state
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "video_url": video_url if video_url else None
        })