import streamlit as st
import requests
import json
import time
from io import BytesIO
from PIL import Image
import base64
import os
from dotenv import load_dotenv
load_dotenv()

# Hardcoded API key (replace with your actual API key)
API_KEY = os.getenv("HEYGEN_API_KEY")

# Simple password for website access
WEBSITE_PASSWORD = "chatbot"  # You can change this to any password you prefer

# Page Configuration
st.set_page_config(
    page_title="Avatar Creator Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1e7dd;
        color: #0f5132;
        margin-top: 1rem;
    }
    .error-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        color: #842029;
        margin-top: 1rem;
    }
    .info-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #cff4fc;
        color: #055160;
        margin-top: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .step-container {
        margin-bottom: 20px;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .step-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .download-button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'active_page' not in st.session_state:
    st.session_state.active_page = "Home"
if 'avatar_id' not in st.session_state:
    st.session_state.avatar_id = None
if 'avatars' not in st.session_state:
    st.session_state.avatars = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'generation_id' not in st.session_state:
    st.session_state.generation_id = None
if 'group_id' not in st.session_state:
    st.session_state.group_id = None
if 'asset_id' not in st.session_state:
    st.session_state.asset_id = None
if 'image_key' not in st.session_state:
    st.session_state.image_key = None
if 'image_keys' not in st.session_state:
    st.session_state.image_keys = []
if 'image_urls' not in st.session_state:
    st.session_state.image_urls = []
if 'selected_image_index' not in st.session_state:
    st.session_state.selected_image_index = None
if 'creation_complete' not in st.session_state:
    st.session_state.creation_complete = False
if 'upload_complete' not in st.session_state:
    st.session_state.upload_complete = False
if 'avatar_name' not in st.session_state:
    st.session_state.avatar_name = ""
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'upload_file' not in st.session_state:
    st.session_state.upload_file = None
if 'appearance' not in st.session_state:
    st.session_state.appearance = ""
if 'training_started' not in st.session_state:
    st.session_state.training_started = False
if 'training_status' not in st.session_state:
    st.session_state.training_status = ""

# API Helper Functions
def get_headers():
    """Get the headers for API requests"""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY
    }

def get_upload_headers(content_type):
    """Get headers for upload API requests"""
    return {
        "Content-Type": content_type,
        "X-Api-Key": API_KEY
    }

def get_recent_avatars(limit=3):
    """Get the most recently created avatars"""
    try:
        # Get all avatar groups
        response = requests.get(
            "https://api.heygen.com/v2/avatar_group.list",
            headers=get_headers()
        )
        
        if response.status_code != 200:
            print(f"Error getting avatar groups: {response.status_code}")
            return []
            
        groups_data = response.json()
        if groups_data.get("error") is not None:
            print(f"Error in groups response: {groups_data.get('error')}")
            return []
            
        # Extract the avatar groups
        avatar_groups = groups_data.get("data", {}).get("avatar_group_list", [])
        print(f"Found {len(avatar_groups)} avatar groups")
        
        # Sort groups by created_at timestamp to get most recent first
        avatar_groups.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        # Get all avatars from all groups
        all_avatars = []
        for group in avatar_groups:
            group_id = group.get("id")
            group_name = group.get("name", "Unknown Group")
            created_at = group.get("created_at", 0)
            
            if not group_id:
                continue
                
            print(f"Checking group: {group_name} (ID: {group_id}, created_at: {created_at})")
                
            # Get avatars for this group
            avatars_response = requests.get(
                f"https://api.heygen.com/v2/avatar_group/{group_id}/avatars",
                headers=get_headers()
            )
            
            if avatars_response.status_code != 200:
                print(f"Error getting avatars for group {group_id}: {avatars_response.status_code}")
                continue
                
            avatars_data = avatars_response.json()
            if avatars_data.get("error") is not None:
                print(f"Error in avatars response for group {group_id}: {avatars_data.get('error')}")
                continue
            
            # Extract avatars from this group
            group_avatars = avatars_data.get("data", {}).get("avatar_list", [])
            print(f"Found {len(group_avatars)} avatars in group {group_name}")
            
            # Add group information and creation timestamp to each avatar
            for avatar in group_avatars:
                avatar["group_name"] = group_name
                avatar["group_id"] = group_id
                avatar["group_created_at"] = created_at
                
            all_avatars.extend(group_avatars)
        
        print(f"Total avatars found: {len(all_avatars)}")
        
        # Sort by group creation date first (most recent groups first), then by avatar ID
        all_avatars.sort(key=lambda x: (x.get('group_created_at', 0), x.get('id', '')), reverse=True)
        
        # Show debug info for top avatars
        for i, avatar in enumerate(all_avatars[:limit]):
            print(f"Recent avatar {i+1}: {avatar.get('name', 'Unnamed')} (ID: {avatar.get('id')}, Group: {avatar.get('group_name')}, Group created: {avatar.get('group_created_at')})")
        
        return all_avatars[:limit]
    except Exception as e:
        print(f"Error getting recent avatars: {str(e)}")
        return []

def search_avatars(search_term):
    """Search avatars by name by first getting avatar groups and then finding avatars within those groups"""
    try:
        # Step 1: Get all avatar groups
        response = requests.get(
            "https://api.heygen.com/v2/avatar_group.list",
            headers=get_headers()
        )
        
        if response.status_code != 200:
            st.error(f"Error fetching avatar groups: Status code {response.status_code}")
            return False
            
        groups_data = response.json()
        if groups_data.get("error") is not None:
            st.error(f"Error fetching avatar groups: {groups_data.get('error')}")
            return False
            
        # Extract the avatar groups
        avatar_groups = groups_data.get("data", {}).get("avatar_group_list", [])
        
        # Step 2: For each group, get the avatars
        all_avatars = []
        for group in avatar_groups:
            group_id = group.get("id")
            if not group_id:
                continue
                
            # Get avatars for this group
            avatars_response = requests.get(
                f"https://api.heygen.com/v2/avatar_group/{group_id}/avatars",
                headers=get_headers()
            )
            
            if avatars_response.status_code != 200:
                continue
                
            avatars_data = avatars_response.json()
            if avatars_data.get("error") is not None:
                continue
            
            # Extract avatars from this group
            group_avatars = avatars_data.get("data", {}).get("avatar_list", [])
            
            # Add group information to each avatar
            for avatar in group_avatars:
                avatar["group_name"] = group.get("name", "Unknown Group")
                avatar["group_id"] = group_id
                
            all_avatars.extend(group_avatars)
        
        # Filter avatars by search term if provided
        if search_term:
            search_term = search_term.lower()
            filtered_avatars = [
                avatar for avatar in all_avatars 
                if search_term in avatar.get('name', '').lower()
            ]
            all_avatars = filtered_avatars
        
        # If no results and we just finished training, add a delay and try again
        if len(all_avatars) == 0 and 'training_status' in st.session_state and st.session_state.training_status == "ready":
            # Add a short delay to allow server indexing
            time.sleep(3)
            # Try the search again (recursive call)
            return search_avatars(search_term)
        
        st.session_state.search_results = all_avatars
        return True
    except Exception as e:
        st.error(f"An error occurred while searching avatars: {str(e)}")
        return False

def upload_asset(file, file_type):
    """Upload a file asset to server"""
    try:
        content_type = f"{file_type}/{file.type.split('/')[-1]}" if file.type else f"{file_type}/octet-stream"
        upload_url = "https://upload.heygen.com/v1/asset"
        
        headers = get_upload_headers(content_type)
        response = requests.post(upload_url, headers=headers, data=file.getvalue())
        
        print(f"Upload response status: {response.status_code}")
        print(f"Upload response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 100:
                asset_info = data.get("data", {})
                asset_id = asset_info.get("id")
                asset_url = asset_info.get("url")
                return True, asset_id, asset_url
            else:
                return False, None, f"Error uploading asset: {data.get('message')}"
        else:
            return False, None, f"Error uploading asset: Status code {response.status_code}"
    except Exception as e:
        return False, None, f"An error occurred while uploading the asset: {str(e)}"

def generate_photo_avatar(avatar_attributes):
    """Generate a photo avatar using HeyGen's AI"""
    try:
        # Create a properly formatted payload according to API docs
        payload = {
            "name": avatar_attributes.get("name", "Generated Avatar"),
            "age": avatar_attributes.get("age"),
            "gender": avatar_attributes.get("gender"),
            "ethnicity": avatar_attributes.get("ethnicity"),
            "orientation": avatar_attributes.get("orientation"),
            "pose": avatar_attributes.get("pose"),
            "style": avatar_attributes.get("style"),
            "appearance": avatar_attributes.get("appearance")
        }
        
        # Debug: Print the request payload
        print("Request payload:", json.dumps(payload, indent=2))
        
        response = requests.post(
            "https://api.heygen.com/v2/photo_avatar/photo/generate",
            headers=get_headers(),
            json=payload
        )
        
        # Debug: Print the response
        print("Response status:", response.status_code)
        print("Response body:", response.text)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("error") is None:
                generation_id = data.get("data", {}).get("generation_id")
                st.session_state.generation_id = generation_id
                return True, generation_id
            else:
                return False, f"Error generating photo avatar: {data.get('error')}"
        else:
            return False, f"Error generating photo avatar: Status code {response.status_code}"
    except Exception as e:
        return False, f"An error occurred while generating the photo avatar: {str(e)}"

def check_photo_generation_status(generation_id):
    """Check the status of a photo generation"""
    try:
        url = f"https://api.heygen.com/v2/photo_avatar/generation/{generation_id}"
        print(f"Checking generation status at URL: {url}")
        
        response = requests.get(
            url,
            headers=get_headers()
        )
        
        print(f"Status check response: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("error") is None:
                status_data = data.get("data", {})
                status = status_data.get("status")
                image_urls = status_data.get("image_url_list")
                image_keys = status_data.get("image_key_list")
                avatar_id = status_data.get("avatar_id")
                
                print(f"Generation status: {status}")
                print(f"Image URLs: {image_urls}")
                print(f"Image keys: {image_keys}")
                print(f"Avatar ID: {avatar_id}")
                
                # Store all image keys and URLs
                if image_keys and len(image_keys) > 0:
                    st.session_state.image_keys = image_keys
                    st.session_state.image_urls = image_urls
                
                # Store avatar_id in session state if available
                if avatar_id:
                    st.session_state.avatar_id = avatar_id
                
                return status, image_urls, image_keys, avatar_id
            else:
                print(f"Error in response: {data.get('error')}")
                return "error", None, None, None
        else:
            print(f"Error response status: {response.status_code}")
            return "error", None, None, None
    except Exception as e:
        print(f"Exception in check_photo_generation_status: {str(e)}")
        return "error", None, None, None

def create_avatar_group(name, image_key, generation_id=None):
    """Create a photo avatar group"""
    try:
        # Ensure the image_key is properly formatted
        # For uploaded photos, image_key should be in the format "image/{asset_id}/original"
        if not image_key.startswith("image/") and not image_key.endswith("/original"):
            # Fix the format if needed
            asset_id = image_key.split("/")[-1] if "/" in image_key else image_key
            image_key = f"image/{asset_id}/original"
            print(f"Reformatted image_key to: {image_key}")
        
        # Prepare the payload based on whether this is an AI-generated avatar or uploaded photo
        payload = {
            "name": name,
            "image_key": image_key
        }
        
        # Add generation_id for AI-generated avatars only if it's provided
        if generation_id:
            payload["generation_id"] = generation_id
            
        print(f"Creating avatar group with payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            "https://api.heygen.com/v2/photo_avatar/avatar_group/create",
            headers=get_headers(),
            json=payload
        )
        
        print(f"Avatar group creation response: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("error") is None:
                group_id = data.get("data", {}).get("group_id")
                st.session_state.group_id = group_id
                return True, group_id
            else:
                return False, f"Error creating avatar group: {data.get('error')}"
        else:
            return False, f"Error creating avatar group: Status code {response.status_code}"
    except Exception as e:
        print(f"Exception in create_avatar_group: {str(e)}")
        return False, f"An error occurred while creating the avatar group: {str(e)}"

def train_avatar_group(group_id):
    """Start training an avatar group"""
    try:
        payload = {
            "group_id": group_id
        }
        
        print(f"Starting training for group_id: {group_id}")
        
        response = requests.post(
            "https://api.heygen.com/v2/photo_avatar/train",
            headers=get_headers(),
            json=payload
        )
        
        print(f"Training response status: {response.status_code}")
        print(f"Training response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("error") is None:
                return True, "Training started successfully"
            else:
                return False, f"Error starting training: {data.get('error')}"
        else:
            return False, f"Error starting training: Status code {response.status_code}"
    except Exception as e:
        print(f"Exception in train_avatar_group: {str(e)}")
        return False, f"An error occurred while starting the training: {str(e)}"

def check_training_status(group_id):
    """Check the status of a group training job"""
    try:
        url = f"https://api.heygen.com/v2/photo_avatar/train/status/{group_id}"
        
        response = requests.get(
            url,
            headers=get_headers()
        )
        
        print(f"Training status check response: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("error") is None:
                status_data = data.get("data", {})
                status = status_data.get("status")
                return status
            else:
                return "error"
        else:
            return "error"
    except Exception as e:
        print(f"Exception in check_training_status: {str(e)}")
        return "error"

def check_api_key_valid():
    """Check if the API key is valid"""
    try:
        # Try to fetch avatar groups as a simple API check
        print("Validating API key...")
        response = requests.get(
            "https://api.heygen.com/v2/avatar_group.list",
            headers=get_headers()
        )
        
        print(f"API key validation response: {response.status_code}")
        print(f"Response content: {response.text[:200]}...") # Print just the beginning to avoid too much output
        
        if response.status_code == 200:
            data = response.json()
            if data.get("error") is None:
                print("API key validation successful")
                return True
                
        print("API key validation failed")
        return False
    except Exception as e:
        print(f"Exception in check_api_key_valid: {str(e)}")
        return False

# Function to generate a download link for an image
def get_image_download_link(img_url, filename):
    """Generate a download link for an image"""
    try:
        response = requests.get(img_url)
        if response.status_code == 200:
            img_data = response.content
            b64 = base64.b64encode(img_data).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="{filename}" class="download-button">Download Image</a>'
            return href
        else:
            return f"<p>Error downloading image: {response.status_code}</p>"
    except Exception as e:
        return f"<p>Error: {str(e)}</p>"

def set_page(page):
    """Set the active page and reset page-specific state"""
    st.session_state.active_page = page
    # Reset page-specific session state when changing pages
    if page != st.session_state.active_page:
        st.session_state.current_step = 1
        if page != "Train Photo into Talking Avatar":
            st.session_state.avatar_name = ""
            st.session_state.upload_file = None
            st.session_state.appearance = ""
            st.session_state.upload_complete = False
            st.session_state.asset_id = None
            st.session_state.image_key = None
            st.session_state.group_id = None
            st.session_state.training_started = False
            st.session_state.training_status = ""
        if page != "Generate Photo with AI":
            st.session_state.generation_id = None
            st.session_state.image_keys = []
            st.session_state.image_urls = []
            st.session_state.selected_image_index = None
            st.session_state.appearance = ""
        if page != "Search Avatars":
            st.session_state.search_results = []
    if page == "Home":
        reset_avatar_creation_state()

def reset_avatar_creation_state():
    """Reset all session state related to avatar creation"""
    keys_to_reset = ['avatar_id', 'generation_id', 'image_keys', 'image_urls', 
                     'selected_image_index', 'creation_complete', 'upload_complete', 
                     'avatar_name', 'current_step', 'upload_file', 
                     'appearance', 'training_started', 'training_status', 'asset_id', 
                     'image_key', 'group_id', 'search_results']
                
    for key in keys_to_reset:
        if key in st.session_state:
            st.session_state[key] = None if key != 'current_step' else 1
    
    st.session_state.image_urls = []
    st.session_state.image_keys = []
    st.session_state.search_results = []

# Main app logic
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Login form
if not st.session_state.authenticated:
    st.markdown("<h1 class='title'>Avatar Creator Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Please enter the password to access the dashboard</p>", unsafe_allow_html=True)
    
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    
    password = st.text_input("Password", type="password", key="login_password")
    login_button = st.button("Login", key="login_submit")
    
    if login_button:
        if password == WEBSITE_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.login_attempts = 0
            st.rerun()
        else:
            st.session_state.login_attempts += 1
            st.error(f"Invalid password. Please try again. (Attempt {st.session_state.login_attempts}/3)")
            
            # Lockout after 3 failed attempts
            if st.session_state.login_attempts >= 3:
                st.error("Too many failed attempts. Please try again later.")
                time.sleep(5)  # Add a delay to discourage brute force attempts
                st.session_state.login_attempts = 0
else:
    # API key validation
    if not check_api_key_valid():
        st.error("Invalid API Key. Please check your hardcoded API key.")
        st.stop()

    # Create a placeholder for main content
    main_content = st.empty()
    
    # Sidebar Navigation
    st.sidebar.title("Avatar Creator")
    
    # Navigation buttons
    if st.sidebar.button("Home", key="home_button"):
        set_page("Home")
        st.rerun()
        
    if st.sidebar.button("Search Avatars", key="search_avatars_button"):
        set_page("Search Avatars")
        st.rerun()
        
    if st.sidebar.button("Train Photo into Talking Avatar", key="train_photo_button"):
        set_page("Train Photo into Talking Avatar")
        st.rerun()
        
    if st.sidebar.button("Generate Photo with AI", key="generate_photo_button"):
        set_page("Generate Photo with AI")
        st.rerun()
    
    # Show current page for debugging
    st.sidebar.text(f"Current page: {st.session_state.active_page}")
    
    # Logout button
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state.authenticated = False
        reset_avatar_creation_state()
        st.rerun()

    # Display content based on active page
    if st.session_state.active_page == "Home":
        with main_content.container():
            st.markdown("<h1 class='title'>Avatar Creator Dashboard</h1>", unsafe_allow_html=True)
            st.markdown("<p class='subtitle'>Create and manage avatars</p>", unsafe_allow_html=True)
            
            # Dashboard overview
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3>Avatar Management</h3>", unsafe_allow_html=True)
            st.markdown("Use this dashboard to:")
            st.markdown("- **Search Avatars**: Find existing avatars by name.")
            st.markdown("- **Train Photo into Talking Avatar**: Upload a photo to create a talking avatar.")
            st.markdown("- **Generate Photo with AI**: Create AI-generated avatar images.")
            st.markdown("- Copy avatar IDs for video generation.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Navigation buttons
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3>Get Started</h3>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Search Avatars", use_container_width=True):
                    set_page("Search Avatars")
                    st.rerun()
            with col2:
                if st.button("Train Photo", use_container_width=True):
                    set_page("Train Photo into Talking Avatar")
                    st.rerun()
            with col3:
                if st.button("Generate AI Photo", use_container_width=True):
                    set_page("Generate Photo with AI")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
    elif st.session_state.active_page == "Search Avatars":
        with main_content.container():
            st.markdown("<h1 class='title'>Search Avatars</h1>", unsafe_allow_html=True)
            st.markdown("<p class='subtitle'>Find your existing avatars</p>", unsafe_allow_html=True)
            
            # Display recent avatars
            st.markdown("### Recently Created Avatars")
            with st.spinner("Loading recent avatars..."):
                recent_avatars = get_recent_avatars(3)
            
            if recent_avatars:
                cols = st.columns(3)
                for i, avatar in enumerate(recent_avatars):
                    with cols[i]:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown(f"<h4>{avatar.get('name', 'Unnamed Avatar')}</h4>", unsafe_allow_html=True)
                        
                        # Display preview image if available
                        preview_url = avatar.get('image_url')
                        if preview_url:
                            st.image(preview_url, use_container_width=True)
                        
                        st.markdown(f"**ID**: `{avatar.get('id', 'N/A')}`")
                        st.markdown(f"**Gender**: {avatar.get('gender', 'Not specified')}")
                        
                        if st.button(f"Select Avatar", key=f"select_recent_avatar_{i}"):
                            st.session_state.avatar_id = avatar.get('id')
                            st.success("Avatar selected successfully!")
                            st.info(f"Selected Avatar ID: `{st.session_state.avatar_id}`")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No recent avatars found.")
            
            st.markdown("---")
            st.markdown("### Search for Specific Avatar")
            
            # Avatar search functionality
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_term = st.text_input("Enter avatar name to search", "")
            with search_col2:
                search_button = st.button("Search")
            
            if search_button and search_term:
                with st.spinner("Searching avatars..."):
                    search_avatars(search_term)
            
            # Display search results
            if st.session_state.search_results:
                st.success(f"Found {len(st.session_state.search_results)} avatars matching your search")
                
                cols = st.columns(3)
                
                for i, avatar in enumerate(st.session_state.search_results):
                    col = cols[i % 3]
                    with col:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown(f"<h4>{avatar.get('name', 'Unnamed Avatar')}</h4>", unsafe_allow_html=True)
                        
                        # Display preview image if available
                        preview_url = avatar.get('image_url')
                        if preview_url:
                            st.image(preview_url, use_container_width=True)
                        
                        st.markdown(f"**ID**: `{avatar.get('id', 'N/A')}`")
                        st.markdown(f"**Gender**: {avatar.get('gender', 'Not specified')}")
                        
                        if st.button(f"Select Avatar", key=f"select_avatar_{i}"):
                            st.session_state.avatar_id = avatar.get('id')
                            st.markdown("<div class='success-message'>Avatar selected successfully!</div>", unsafe_allow_html=True)
                            st.markdown(f"Selected Avatar ID: `{st.session_state.avatar_id}`")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            elif search_button and search_term:
                st.info(f"No avatars found matching '{search_term}'")
            else:
                st.info("Enter an avatar name and click 'Search' to find avatars.")
    
    elif st.session_state.active_page == "Train Photo into Talking Avatar":
        with main_content.container():
            st.markdown("<h1 class='title'>Train Photo into Talking Avatar</h1>", unsafe_allow_html=True)
            st.markdown("<p class='subtitle'>Create a talking avatar from a photo</p>", unsafe_allow_html=True)
            
            # Step 1: Enter avatar name
            if st.session_state.current_step == 1:
                st.markdown("<div class='step-container'>", unsafe_allow_html=True)
                st.markdown("<div class='step-header'>Step 1: Enter Avatar Name</div>", unsafe_allow_html=True)
                
                avatar_name = st.text_input("Avatar Name", value=st.session_state.avatar_name)
                
                if st.button("Continue to Step 2", use_container_width=True):
                    if not avatar_name:
                        st.error("Please enter an avatar name.")
                    else:
                        st.session_state.avatar_name = avatar_name
                        st.session_state.current_step = 2
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Step 2: Upload photo and appearance description
            elif st.session_state.current_step == 2:
                st.markdown("<div class='step-container'>", unsafe_allow_html=True)
                st.markdown("<div class='step-header'>Step 2: Upload Photo</div>", unsafe_allow_html=True)
                
                if st.button("← Back to Step 1", key="back_to_step1"):
                    st.session_state.current_step = 1
                    st.rerun()
                
                st.info("Upload a photo with a clear view of the face.")
                
                uploaded_file = st.file_uploader("Upload Photo (JPG, PNG)", type=["jpg", "jpeg", "png"])
                
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Preview", width=300)
                    st.session_state.upload_file = uploaded_file
                
                st.markdown("### Appearance Description")
                appearance = st.text_area(
                    "Describe how you want your avatar to appear (clothing, background, etc.)",
                    value=st.session_state.appearance,
                    help="This description will be used to customize your avatar's appearance."
                )
                
                if st.button("Continue to Step 3", use_container_width=True):
                    if not uploaded_file:
                        st.error("Please upload a photo.")
                    elif not appearance:
                        st.error("Please provide an appearance description.")
                    else:
                        st.session_state.appearance = appearance
                        with st.spinner("Uploading photo..."):
                            success, asset_id, asset_url = upload_asset(uploaded_file, "image")
                            
                            if success:
                                st.session_state.asset_id = asset_id
                                st.session_state.image_key = f"image/{asset_id}/original"
                                st.success(f"Photo uploaded successfully! Asset ID: {asset_id}")
                                st.info(f"Image Key: {st.session_state.image_key}")
                                st.info(f"Image URL: {asset_url}")
                                if asset_url:
                                    st.image(asset_url, caption="Uploaded Image", width=300)
                                st.session_state.upload_complete = True
                                st.session_state.current_step = 3
                                st.rerun()
                            else:
                                st.error(asset_url)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Step 3: Create and train avatar group
            elif st.session_state.current_step == 3:
                st.markdown("<div class='step-container'>", unsafe_allow_html=True)
                st.markdown("<div class='step-header'>Step 3: Create and Train Avatar</div>", unsafe_allow_html=True)
                
                if st.button("← Back to Step 2", key="back_to_step2"):
                    st.session_state.current_step = 2
                    st.rerun()
                
                if st.session_state.upload_complete:
                    st.success("Photo uploaded successfully!")
                    st.info(f"Asset ID: {st.session_state.asset_id}")
                    st.info(f"Image Key: {st.session_state.image_key}")
                    
                    if st.button("Create Avatar Group", use_container_width=True):
                        if not st.session_state.image_key.startswith("image/") or not st.session_state.image_key.endswith("/original"):
                            st.session_state.image_key = f"image/{st.session_state.asset_id}/original"
                            st.warning(f"Image key format corrected to: {st.session_state.image_key}")
                        
                        with st.spinner("Creating avatar group..."):
                            success, group_id = create_avatar_group(
                                st.session_state.avatar_name,
                                st.session_state.image_key
                            )
                            
                            if success:
                                st.session_state.group_id = group_id
                                st.success(f"Avatar group created successfully! Group ID: {group_id}")
                                st.session_state.training_started = False
                                st.rerun()
                            else:
                                st.error(group_id)
                                st.error("Error creating avatar group. Possible issues:")
                                st.error("1. The image format may not be supported")
                                st.error("2. The image may not contain a clear face")
                                st.error("3. The image_key format might be incorrect")
                                st.error("Try uploading a different image with a clear frontal face")
                
                if st.session_state.group_id:
                    st.subheader("Train Your Avatar")
                    st.info("Training allows your avatar to capture facial features and expressions.")
                    
                    if not st.session_state.training_started:
                        if st.button("Start Training", use_container_width=True):
                            with st.spinner("Starting training process..."):
                                success, message = train_avatar_group(st.session_state.group_id)
                                
                                if success:
                                    st.session_state.training_started = True
                                    st.session_state.training_status = "in_progress"
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                    else:
                        status_placeholder = st.empty()
                        with status_placeholder:
                            st.info("Checking training status...")
                        
                        status = check_training_status(st.session_state.group_id)
                        
                        if status == "ready":
                            status_placeholder.success("Training completed successfully!")
                            st.session_state.training_status = "ready"
                            
                            avatar_info = {
                                'avatar_id': st.session_state.avatar_id,
                                'avatar_name': st.session_state.avatar_name,
                            }
                            
                            st.session_state.search_results.append(avatar_info)
                            
                            st.markdown("""
                            ### Your avatar has been created and trained successfully!
                            
                            You can now use this avatar in your videos. Search for your avatar by name
                            in the 'Search Avatars' page.
                            """)
                            
                            if st.button("Create Another Avatar", use_container_width=True):
                                reset_avatar_creation_state()
                                st.session_state.current_step = 1
                                st.rerun()
                                
                        elif status == "error":
                            status_placeholder.error("Training failed. Please try again.")
                            st.session_state.training_status = "error"
                        else:
                            status_placeholder.info("Training is still in progress. This may take several minutes.")
                            st.session_state.training_status = "in_progress"
                            
                            if st.button("Refresh Training Status", use_container_width=True):
                                st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='info-message'>", unsafe_allow_html=True)
                st.markdown("""
                **Tips for Avatar Training**:
                - Training usually takes 5-10 minutes to complete
                - Once training is complete, you can use your avatar in videos
                - More detailed appearance descriptions lead to better results
                - You can create multiple looks for your avatar after training
                """)
                st.markdown("</div>", unsafe_allow_html=True)
    
    elif st.session_state.active_page == "Generate Photo with AI":
        with main_content.container():
            st.markdown("<h1 class='title'>Generate Photo with AI</h1>", unsafe_allow_html=True)
            st.markdown("<p class='subtitle'>Create AI-generated avatar images</p>", unsafe_allow_html=True)
            
            # Step 1: Enter AI generation attributes
            if st.session_state.current_step == 1:
                st.markdown("<div class='step-container'>", unsafe_allow_html=True)
                st.markdown("<div class='step-header'>Step 1: Generate AI Avatar</div>", unsafe_allow_html=True)
                
                st.info("Generate AI avatars by providing detailed attributes and appearance description.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    age = st.selectbox(
                        "Age", 
                        ["Young Adult", "Early Middle Age", "Late Middle Age", "Senior", "Unspecified"],
                        help="Select the approximate age of your avatar"
                    )
                    
                    gender = st.selectbox(
                        "Gender", 
                        ["Woman", "Man"],
                        help="Select the gender of your avatar"
                    )
                    
                    ethnicity = st.selectbox(
                        "Ethnicity", 
                        [
                            "Asian American", 
                            "African American", 
                            "European American", 
                            "Hispanic American", 
                            "Middle Eastern", 
                            "South Asian"
                        ],
                        help="Select the ethnicity of your avatar"
                    )
                
                with col2:
                    orientation = st.selectbox(
                        "Orientation", 
                        ["horizontal", "vertical"],
                        help="Select the orientation of the generated image"
                    )
                    
                    pose = st.selectbox(
                        "Pose", 
                        ["half_body", "head_shot", "full_body"],
                        help="Select the pose type for your avatar"
                    )
                    
                    style = st.selectbox(
                        "Style", 
                        ["Realistic", "Cartoon", "3D", "Anime"],
                        help="Select the visual style of your avatar"
                    )
                
                st.markdown("### Avatar Name")
                avatar_name = st.text_input(
                    "Enter a name for your avatar",
                    value="Generated Avatar",
                    help="This name will be used to identify your avatar"
                )
                
                st.markdown("### Appearance Description")
                appearance = st.text_area(
                    "Describe your avatar's appearance in detail",
                    value=st.session_state.appearance if st.session_state.appearance else "A professional looking person in business attire with a friendly expression",
                    help="Be specific about clothing, expression, accessories, etc."
                )
                
                if st.button("Generate Images", use_container_width=True):
                    if not avatar_name:
                        st.error("Please provide an avatar name.")
                    elif not appearance:
                        st.error("Please provide an appearance description.")
                    else:
                        st.session_state.appearance = appearance
                        st.session_state.avatar_attributes = {
                            "name": avatar_name,
                            "age": age,
                            "gender": gender,
                            "ethnicity": ethnicity,
                            "orientation": orientation,
                            "pose": pose,
                            "style": style,
                            "appearance": appearance
                        }
                        
                        with st.spinner("Generating AI photo avatar..."):
                            success, result = generate_photo_avatar(
                                st.session_state.avatar_attributes
                            )
                            
                            if success:
                                st.session_state.generation_id = result
                                st.session_state.current_step = 2
                                st.rerun()
                            else:
                                st.error(result)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Step 2: Display and download generated images
            elif st.session_state.current_step == 2:
                st.markdown("<div class='step-container'>", unsafe_allow_html=True)
                st.markdown("<div class='step-header'>Step 2: Download Generated Images</div>", unsafe_allow_html=True)
                
                if st.button("← Back to Step 1", key="back_to_step1"):
                    st.session_state.current_step = 1
                    st.rerun()
                
                if st.session_state.generation_id:
                    status_placeholder = st.empty()
                    progress_placeholder = st.empty()
                    
                    with status_placeholder:
                        st.info("Checking generation status...")
                    
                    progress_bar = progress_placeholder.progress(0)
                    
                    attempt = 0
                    max_attempts = 60
                    
                    while attempt < max_attempts:
                        attempt += 1
                        progress = min(0.95, attempt / max_attempts)
                        progress_bar.progress(progress)
                        
                        status, image_urls, image_keys, avatar_id = check_photo_generation_status(
                            st.session_state.generation_id
                        )
                        
                        if status == "success":
                            progress_bar.progress(1.0)
                            status_placeholder.success("Images generated successfully!")
                            
                            st.subheader("Generated Images:")
                            
                            if image_urls and len(image_urls) > 0:
                                cols = st.columns(min(2, len(image_urls)))
                                
                                for i, url in enumerate(image_urls):
                                    with cols[i % len(cols)]:
                                        st.image(url, caption=f"Generated Image {i+1}", use_container_width=True)
                                        download_link = get_image_download_link(url, f"AI_Avatar_image_{i+1}.jpg")
                                        st.markdown(download_link, unsafe_allow_html=True)
                            
                            if st.button("Generate More Images", use_container_width=True):
                                reset_avatar_creation_state()
                                st.session_state.current_step = 1
                                st.rerun()
                            
                            if st.button("Start Over", use_container_width=True):
                                reset_avatar_creation_state()
                                st.session_state.current_step = 1
                                st.rerun()
                            
                            break
                        
                        elif status == "error":
                            progress_bar.progress(1.0)
                            status_placeholder.error("Generation failed. Please try again.")
                            break
                        
                        time.sleep(5)
                    
                    if status != "success" and status != "error":
                        status_placeholder.warning("Generation is still in progress. Please wait...")
                
                st.markdown("<div class='info-message'>", unsafe_allow_html=True)
                st.markdown("""
                **Tips for AI Generated Photos**:
                - Download your favorite images to use in other applications
                - Try different appearance descriptions for varied results
                - You can generate multiple sets of images with different settings
                - To create a talking avatar, use the "Train Photo into Talking Avatar" page
                """)
                st.markdown("</div>", unsafe_allow_html=True)