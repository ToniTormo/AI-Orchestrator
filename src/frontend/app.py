"""
Streamlit Frontend Application

Provides a user interface for the AI orchestration system
"""

import streamlit as st
import asyncio
import time
import base64
import threading
import nest_asyncio
from pathlib import Path
from src.utils.logging import setup_logger

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Import orchestration system components
from src.cli.cli_helpers import orchestrate_tasks

# Set page configuration
st.set_page_config(
    page_title="AI Project Orchestration System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Get the absolute path to the resources directory
resources_dir = Path(__file__).parent / "resources"

# Function to encode image to base64
def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Get base64 encoded images
try:
    bg_loby = get_base64_encoded_image(resources_dir / "background_loby.png")
    bg_loading = get_base64_encoded_image(resources_dir / "background_loading.png")
    logo_white = get_base64_encoded_image(resources_dir / "Logo_white.png")
    logo_black = get_base64_encoded_image(resources_dir / "Logo_black.png")
except Exception as e:
    st.error(f"Error loading images: {e}")
    bg_loby = ""
    bg_loading = ""
    logo_white = ""
    logo_black = ""

# Custom CSS for improved styling
st.markdown(f"""
<style>
    /* Fix page to prevent scrolling */
    html, body, [class*="css"] {{
        color: #333333;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        height: 100vh;
        overflow: hidden;
    }}
    
    /* Reset Streamlit's default styling */
    .stApp {{
        background-color: transparent;
        height: 100vh;
        overflow: hidden;
    }}
    
    /* Main backgrounds */
    .main-bg {{
        background-image: url("data:image/png;base64,{bg_loby}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
    }}
    
    .loading-bg {{
        background-image: url("data:image/png;base64,{bg_loading}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
    }}
    
    /* Logos */
    .logo-white {{
        position: fixed;
        top: 20px;
        left: 20px;
        width: 150px;
        z-index: 1000;
    }}
    
    .logo-black {{
        position: fixed;
        top: 20px;
        left: 20px;
        width: 150px;
        z-index: 1000;
    }}
    
    /* Text styling */
    .main-header {{
        font-size: 2.5rem;
        color: #ffffff;
        margin-bottom: 1rem;
        font-weight: bold;
        text-align: center;
        margin-top: 50px;
    }}
    
    .sub-header {{
        font-size: 1.5rem;
        color: #ffffff;
        margin-bottom: 2rem;
        text-align: center;
    }}
    
    /* Form styling */
    .form-container {{
        background-color: rgba(23, 24, 34, 0.7);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 12px;
        max-width: 800px;
        margin: 0 auto;
        margin-top: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        border: none;
    }}
    
    /* Input fields */
    .stTextInput > div > div > input {{
        background-color: white;
        color: #333 !important;
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 12px 15px;
    }}
    
    .stTextArea > div > div > textarea {{
        background-color: white;
        color: #333 !important;
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 12px 15px;
        min-height: 150px;
    }}
    
    /* Labels */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label {{
        color: white !important;
        font-weight: 500;
    }}
    
    /* Button styling */
    .stButton > button {{
        width: 60%;
        margin: 0 auto;
        display: block;
        background-color: #F0FF3D;
        color: #0B3142;
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 15px;
    }}
    
    .stButton > button:hover {{
        background-color: #E6FF00;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}
    
    /* Loading animation */
    .loading-spinner {{
        text-align: center;
        margin: 100px auto;
    }}
    
    /* Custom progress bar */
    .custom-progress {{
        width: 50%;
        height: 20px;
        margin: 50px auto;
        background-color: #f3f3f3;
        border-radius: 10px;
        overflow: hidden;
    }}
    
    .progress-bar {{
        height: 100%;
        background-color: #162532;
        border-radius: 10px;
        transition: width 0.5s ease;
    }}
    
    /* Override any dark mode settings */
    .stMarkdown {{
        color: white;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

def get_viability_class(score: int) -> str:
    """Get CSS class based on viability score"""
    if score >= 80:
        return "viability-high"
    elif score >= 60:
        return "viability-medium"
    else:
        return "viability-low"

def run_async_task(func, callback=None, *args, **kwargs):
    """Run an async task in a separate thread and call the callback when done"""
    result_container = {}
    
    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(func(*args, **kwargs))
            result_container['result'] = result
            result_container['error'] = None
        except Exception as e:
            result_container['result'] = None
            result_container['error'] = str(e)
        finally:
            loop.close()
            if callback:
                callback(result_container)
    
    thread = threading.Thread(target=thread_target)
    thread.start()
    return thread, result_container

def main():
    """Main Streamlit application"""
    # Initialize session state for multi-page logic
    if 'page' not in st.session_state:
        st.session_state.page = 'input'
    
    if 'evaluation_result' not in st.session_state:
        st.session_state.evaluation_result = None
    
    if 'processing_result' not in st.session_state:
        st.session_state.processing_result = None
    
    if 'error' not in st.session_state:
        st.session_state.error = None
    
    # Function to handle page navigation
    def go_to_page(page_name):
        st.session_state.page = page_name
    
    # Input Page
    if st.session_state.page == 'input':
        # Add background and logo
        st.markdown('<div class="main-bg"></div>', unsafe_allow_html=True)
        st.markdown(f'<img src="data:image/png;base64,{logo_white}" class="logo-white" alt="Logo">', unsafe_allow_html=True)
        
        # Main header and subheader
        st.markdown('<h1 class="main-header">AI Project Orchestration System</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Automate the analysis, modification and orchestration of projects with AI</p>', unsafe_allow_html=True)
        
        # Input form with styled container - removed the extra container/box
        with st.form(key='project_form'):
            col1, col2 = st.columns(2)
            
            with col1:
                repo_url = st.text_input("Repository URL", 
                                         placeholder="https://github.com/username/repository.git")
            
            with col2:
                branch = st.text_input("Branch", value="main", 
                                       placeholder="main, develop, feature/xyz")
            
            change_request = st.text_area("Change Description", 
                                          placeholder="Describe a project and let AI handle it for you...")
            
            submit_button = st.form_submit_button("Evaluate Project")
            
            if submit_button and repo_url and change_request:
                with st.spinner("Cloning and analyzing repository..."):
                    # Reset previous results
                    st.session_state.evaluation_result = None
                    st.session_state.error = None
                    
                    # Start evaluation in background
                    def on_evaluation_complete(result_container):
                        if result_container.get('error'):
                            st.session_state.error = result_container['error']
                        else:
                            st.session_state.evaluation_result = result_container['result']
                        go_to_page('viability')
                        st.rerun()
                    
                    run_async_task(
                        setup_repository,
                        on_evaluation_complete,
                        repo_url=repo_url,
                        change_request=change_request,
                        branch=branch
                    )
                    
                    # Show loading placeholder while evaluating
                    for _ in range(3):
                        time.sleep(0.5)
                        st.spinner("Cloning and analyzing repository...")
                    
                    # Go to loading page
                    go_to_page('loading')
                    st.rerun()
            
            elif submit_button:
                st.error("Please complete all required fields.")
    
    # Loading Page
    elif st.session_state.page == 'loading':
        # Add loading background and logo
        st.markdown('<div class="loading-bg"></div>', unsafe_allow_html=True)
        st.markdown(f'<img src="data:image/png;base64,{logo_black}" class="logo-black" alt="Logo">', unsafe_allow_html=True)
        
        # Loading content
        st.markdown('<h2 style="text-align: center; color: #000; margin-top: 50px;">Working on the project</h2>', unsafe_allow_html=True)
        
        # Custom, shorter progress bar
        st.markdown('<div class="custom-progress">', unsafe_allow_html=True)
        
        # Number of steps to show in progress
        steps = 5
        time_per_step = 2  # seconds per step
        
        # Progress placeholder
        progress_placeholder = st.empty()
        
        # Simulate progress more slowly
        for i in range(steps):
            progress_percentage = (i + 1) / steps * 100
            progress_placeholder.markdown(
                f'<div class="custom-progress"><div class="progress-bar" style="width: {progress_percentage}%;"></div></div>',
                unsafe_allow_html=True
            )
            time.sleep(time_per_step)
        
        # This should only run if something went wrong with the callback
        if st.session_state.evaluation_result is not None:
            go_to_page('viability')
            st.rerun()
        elif st.session_state.error is not None:
            go_to_page('error')
            st.rerun()
    
    # Viability Assessment Page
    elif st.session_state.page == 'viability':
        # Add background and logo
        st.markdown('<div class="main-bg"></div>', unsafe_allow_html=True)
        st.markdown(f'<img src="data:image/png;base64,{logo_white}" class="logo-white" alt="Logo">', unsafe_allow_html=True)
        
        if st.session_state.evaluation_result is not None:
            result = st.session_state.evaluation_result
            viability = result['viability_result']
            project_details = result['project_details']
            
            # Main title
            st.markdown('<h2 style="color: white; text-align: center; margin-top: 30px;">Viability Assessment</h2>', unsafe_allow_html=True)
            
            # Display results in a styled container
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            
            # Display viability score
            score = viability['score']
            score_class = get_viability_class(score)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <h3 style="color: white;">Project: {project_details['name']}</h3>
                <p style="color: #CCC;">Requested changes: {project_details['change_request']}</p>
                <p style="color: white;">Viability score: <span class="{score_class}">{score}%</span></p>
                <p style="color: white;">Prediction confidence: {viability['confidence']}%</p>
                """, unsafe_allow_html=True)
            
            with col2:
                # Visualize score with gauge or progress
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <h4 style="color: white;">Viability</h4>
                    <div style="font-size: 3rem; font-weight: bold;" class="{score_class}">{score}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display detailed factors
            st.markdown("<h3 style='color: white; margin-top: 20px;'>Viability Factors</h3>", unsafe_allow_html=True)
            
            factors = viability['factors']
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                factor_class = get_viability_class(factors['complexity'])
                st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <h5 style="color: white;">Complexity</h5>
                    <div class="{factor_class}">{factors['complexity']}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                factor_class = get_viability_class(factors['clarity'])
                st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <h5 style="color: white;">Clarity</h5>
                    <div class="{factor_class}">{factors['clarity']}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                factor_class = get_viability_class(factors['technical_feasibility'])
                st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <h5 style="color: white;">Technical Feasibility</h5>
                    <div class="{factor_class}">{factors['technical_feasibility']}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                factor_class = get_viability_class(factors['resource_availability'])
                st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <h5 style="color: white;">Resource Availability</h5>
                    <div class="{factor_class}">{factors['resource_availability']}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display recommendations
            if 'recommendations' in viability and viability['recommendations']:
                st.markdown("<h3 style='color: white; margin-top: 20px;'>Recommendations</h3>", unsafe_allow_html=True)
                for rec in viability['recommendations']:
                    st.markdown(f"<p style='color: #CCC;'>• {rec}</p>", unsafe_allow_html=True)
            
            # Technologies detected
            if 'technologies' in project_details:
                st.markdown("<h3 style='color: white; margin-top: 20px;'>Detected Technologies</h3>", unsafe_allow_html=True)
                tech = project_details['technologies']
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.75rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                        <h5 style="color: white;">Frontend</h5>
                        <div style="color: #CCC;">{tech.get('frontend', 'Not detected')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.75rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                        <h5 style="color: white;">Backend</h5>
                        <div style="color: #CCC;">{tech.get('backend', 'Not detected')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.75rem; background-color: rgba(30, 32, 44, 0.8); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                        <h5 style="color: white;">Database</h5>
                        <div style="color: #CCC;">{tech.get('database', 'Not detected')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Action buttons
            st.markdown("<h3 style='color: white; margin-top: 25px;'>Do you want to continue with the project?</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⬅️ Go Back and Redefine", key="back_button"):
                    go_to_page('input')
                    st.rerun()
            
            with col2:
                if st.button("✅ Continue and Process", key="continue_button"):
                    # Process the project
                    with st.spinner("Processing the project..."):
                        # Start processing in background
                        def on_processing_complete(result_container):
                            if result_container.get('error'):
                                st.session_state.error = result_container['error']
                                go_to_page('error')
                            else:
                                st.session_state.processing_result = result_container['result']
                                go_to_page('success')
                            st.rerun()
                        
                        repo_url = project_details['repository']
                        change_request = project_details['change_request']
                        branch = project_details['branch']
                        
                        run_async_task(
                            orchestrate_tasks,
                            on_processing_complete,
                            repo_url=repo_url,
                            change_request=change_request,
                            branch=branch
                        )
                        
                        # Go to processing page
                        go_to_page('processing')
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True) # Close form container
        else:
            st.error("No evaluation results available")
            if st.button("Back to start"):
                go_to_page('input')
                st.rerun()
    
    # Processing Page
    elif st.session_state.page == 'processing':
        # Add loading background and logo
        st.markdown('<div class="loading-bg"></div>', unsafe_allow_html=True)
        st.markdown(f'<img src="data:image/png;base64,{logo_black}" class="logo-black" alt="Logo">', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center; color: #000; margin-top: 50px;">Processing Changes</h2>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #333; margin-bottom: 30px;">We are analyzing, implementing and testing the requested changes. This process may take a few minutes.</p>', unsafe_allow_html=True)
        
        # Custom, shorter progress bar
        st.markdown('<div class="custom-progress">', unsafe_allow_html=True)
        
        # Number of steps in processing
        steps = 5
        time_per_step = 3  # seconds per step
        phases = [
            "Analyzing repository",
            "Planning tasks",
            "Generating code",
            "Running tests",
            "Finalizing changes"
        ]
        
        # Progress and phase placeholder
        progress_placeholder = st.empty()
        phase_placeholder = st.empty()
        
        # Simulate progress more slowly with phases
        for i, phase in enumerate(phases):
            # Update phase text
            phase_placeholder.markdown(f'<h4 style="text-align: center; color: #333;">Phase: {phase}</h4>', unsafe_allow_html=True)
            
            # Update progress bar
            progress_percentage = (i + 1) / steps * 100
            progress_placeholder.markdown(
                f'<div class="custom-progress"><div class="progress-bar" style="width: {progress_percentage}%;"></div></div>',
                unsafe_allow_html=True
            )
            
            # Wait for this phase to complete
            time.sleep(time_per_step)
        
        # This should only run if something went wrong with the callback
        if st.session_state.processing_result is not None:
            go_to_page('success')
            st.rerun()
        elif st.session_state.error is not None:
            go_to_page('error')
            st.rerun()
    
    # Success Page
    elif st.session_state.page == 'success':
        # Add background and logo
        st.markdown('<div class="main-bg"></div>', unsafe_allow_html=True)
        st.markdown(f'<img src="data:image/png;base64,{logo_white}" class="logo-white" alt="Logo">', unsafe_allow_html=True)
        
        if st.session_state.processing_result is not None:
            result = st.session_state.processing_result
            
            st.markdown('<h2 style="color: white; text-align: center; margin-top: 30px;">Changes Applied Successfully!</h2>', unsafe_allow_html=True)
            st.markdown('<p style="color: white; text-align: center;">The requested changes have been implemented in the repository.</p>', unsafe_allow_html=True)
            
            # Display results in a styled container
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            
            # Display summary of changes
            if 'modified_files' in result:
                st.markdown(f"<h3 style='color: white;'>Modified Files: {len(result['modified_files'])}</h3>", unsafe_allow_html=True)
                for file in result['modified_files']:
                    st.markdown(f"<p style='color: #CCC;'>• <code style='background: rgba(255,255,255,0.1); padding: 2px 5px; border-radius: 3px;'>{file}</code></p>", unsafe_allow_html=True)
            
            # Display commit information
            if 'commit_hash' in result:
                st.markdown(f"<h3 style='color: white;'>Commit Hash</h3><p><code style='background: rgba(255,255,255,0.1); padding: 5px 8px; border-radius: 4px; color: #CCC;'>{result['commit_hash']}</code></p>", unsafe_allow_html=True)
            
            # Notification about email
            st.markdown(render_notification_email(), unsafe_allow_html=True)
            
            # Push button (optional)
            if st.button("Push changes to remote repository"):
                st.warning("This functionality would require additional configuration for Git credentials")
            
            # New project button
            if st.button("Start New Project"):
                # Reset all state and go back to input
                st.session_state.evaluation_result = None
                st.session_state.processing_result = None
                st.session_state.error = None
                go_to_page('input')
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True) # Close form container
        else:
            st.error("No processing results available")
            if st.button("Back to start"):
                go_to_page('input')
                st.rerun()
    
    # Error Page
    elif st.session_state.page == 'error':
        # Add background and logo
        st.markdown('<div class="main-bg"></div>', unsafe_allow_html=True)
        st.markdown(f'<img src="data:image/png;base64,{logo_white}" class="logo-white" alt="Logo">', unsafe_allow_html=True)
        
        st.markdown('<h2 style="color: white; text-align: center; margin-top: 30px;">Error in Processing</h2>', unsafe_allow_html=True)
        
        # Display error in a styled container
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
        if st.session_state.error:
            st.error(st.session_state.error)
        else:
            st.error("An unknown error occurred during processing")
        
        if st.button("Back to start"):
            # Reset error state and go back to input
            st.session_state.error = None
            go_to_page('input')
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True) # Close form container

def render_notification_email():
    """Render the notification email template"""
    return f"""
    <div style="background-color: rgba(30, 32, 44, 0.8); padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid rgba(255, 255, 255, 0.1);">
        <h4 style="color: white; margin-top: 0;">Notification</h4>
        {render_notification_email_content()}
    </div>
    """

def render_notification_email_content():
    """Render the notification email content"""
    return f"""
    <p style="color: #CCC;">An email will be sent to {settings.notification.email} when the process is fully completed.</p>
    """

if __name__ == "__main__":
    main()