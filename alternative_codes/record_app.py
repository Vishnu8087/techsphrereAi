import streamlit as st
from modules.record import list_devices  # Assuming start_recording is no longer needed
from modules.process_video import upload_and_process_video, summarize_video
from modules.process_video import generate_mcqs
from modules.generate_descriptive import generate_descriptive_questions, extract_markdown_to_text
from modules.validate_answers import process_student_papers
from modules.pgoogle_form import create_google_form
from modules.google_classroom import list_courses_with_urls
import os
import subprocess
import time
import threading

# Streamlit App Configuration
st.set_page_config(page_title="Educational Video Tool", layout="wide")
st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to", [
    "Record Video",
    "Process Video",
    "Summarize Video",
    "Generate MCQs",
    "Generate Descriptive Questions",
    "Evaluate Answers",
    "Create Google Form",
    "Google Classroom Integration"
])

# Helper function to play recording
def play_recording(file_path):
    if not os.path.exists(file_path):
        st.error(f"Video file {file_path} not found!")
        return
    
    # Primary playback via Streamlit
    st.write(f"Playing {file_path} in Streamlit:")
    st.video(file_path)

    # Optional FFplay attempt with error handling
    try:
        st.write("Attempting FFplay playback (optional)...")
        process = subprocess.Popen(
            ["ffplay", file_path, "-autoexit"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate(timeout=5)
        if process.returncode != 0:
            st.warning(f"FFplay failed: {stderr}. Using Streamlit player instead.")
        else:
            st.write("FFplay playback initiated (check your system).")
    except FileNotFoundError:
        st.warning("FFplay not found. Ensure FFmpeg is installed if you want FFplay support.")
    except subprocess.TimeoutExpired:
        st.warning("FFplay timed out; sticking with Streamlit player.")
        process.kill()

# Section 1: Record Video
if section == "Record Video":
    st.header("Record Video")
    video_devices, audio_devices = list_devices()
    
    if not video_devices or not audio_devices:
        st.error("No video or audio devices found!")
    else:
        st.subheader("Select Devices")
        video_device = st.selectbox("Video Device", video_devices)
        audio_device = st.selectbox("Audio Device", audio_devices)
        
        output_file = "output.mkv"

        # Session state for recording control
        if "recording_process" not in st.session_state:
            st.session_state.recording_process = None
            st.session_state.is_recording = False

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Recording", disabled=st.session_state.is_recording):
                if os.path.exists(output_file):
                    os.remove(output_file)  # Clear previous file
                st.write("Starting recording...")

                def run_recording():
                    process = subprocess.Popen([
                        "ffmpeg", "-f", "dshow", "-rtbufsize", "100M",
                        "-i", f"video={video_device}:audio={audio_device}",
                        "-pix_fmt", "yuv420p", "-s", "640x480", "-r", "25",
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-b:v", "1M",
                        "-c:a", "aac", "-b:a", "128k", "-map", "0:v", "-map", "0:a",
                        output_file
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    st.session_state.recording_process = process
                    process.wait()

                threading.Thread(target=run_recording, daemon=True).start()
                st.session_state.is_recording = True
                st.success("Recording started. Use 'Stop Recording' to end.")

        with col2:
            if st.button("Stop Recording", disabled=not st.session_state.is_recording):
                if st.session_state.recording_process:
                    try:
                        st.session_state.recording_process.terminate()
                        st.session_state.recording_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        st.session_state.recording_process.kill()
                        st.warning("Recording forcefully terminated.")
                    
                    st.session_state.is_recording = False
                    st.session_state.recording_process = None
                    
                    time.sleep(1)  # Allow file to finalize
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                        st.success(f"Recording saved as {output_file}")
                    else:
                        st.error("Recording stopped, but the file may be empty or corrupted.")
                else:
                    st.error("No recording process to stop!")

        if os.path.exists(output_file) and not st.session_state.is_recording:
            if st.button("Play Recording"):
                play_recording(output_file)

# Section 2: Process Video
if section == "Process Video":
    st.header("Process Video")
    video_file = st.file_uploader("Upload Video File", type=["mp4", "mkv"])
    if video_file:
        video_path = f"uploaded_video_{int(time.time())}.mp4"
        with open(video_path, "wb") as f:
            f.write(video_file.read())
        st.success(f"Video uploaded: {video_path}")
        
        with st.spinner("Processing video..."):
            video_uri = upload_and_process_video(video_path)
            st.write(f"Video processed: {video_uri}")
            st.session_state["video_uri"] = video_uri

# Section 3: Summarize Video
if section == "Summarize Video":
    st.header("Summarize Video")
    if "video_uri" not in st.session_state:
        st.warning("Please process a video first!")
    else:
        if st.button("Generate Summary"):
            with st.spinner("Generating summary..."):
                summary = summarize_video(st.session_state["video_uri"])
                st.markdown(summary)

# Section 4: Generate MCQs
if section == "Generate MCQs":
    st.header("Generate Multiple Choice Questions")
    if "video_uri" not in st.session_state:
        st.warning("Please process a video first!")
    else:
        num_mcqs = st.number_input("Number of MCQs", min_value=1, max_value=50, value=20)
        difficulty = st.selectbox("Difficulty Level", ["easy", "medium", "hard"])
        if st.button("Generate MCQs"):
            with st.spinner("Generating MCQs..."):
                mcq_text = generate_mcqs(st.session_state["video_uri"], num_mcqs, difficulty)
                st.markdown(mcq_text)
                with open("mcq_questions.txt", "w", encoding="utf-8") as f:
                    f.write(mcq_text)
                st.success("MCQs saved to mcq_questions.txt")

# Section 5: Generate Descriptive Questions
if section == "Generate Descriptive Questions":
    st.header("Generate Descriptive Questions")
    if "video_uri" not in st.session_state:
        st.warning("Please process a video first!")
    else:
        num_questions = st.number_input("Number of Questions", min_value=1, max_value=10, value=3)
        if st.button("Generate Questions"):
            with st.spinner("Generating questions..."):
                descriptive_text = generate_descriptive_questions(st.session_state["video_uri"], num_questions)
                st.markdown(descriptive_text)
                extract_markdown_to_text(descriptive_text, "questions.txt", "answers.txt")
                st.success("Questions and answers saved to questions.txt and answers.txt")

# Section 6: Evaluate Answers
if section == "Evaluate Answers":
    st.header("Evaluate Descriptive Answers")
    key_file = st.file_uploader("Upload Key Answer File (.docx)", type=["docx"])
    student_files = st.file_uploader("Upload Student Answer Files (.docx)", type=["docx"], accept_multiple_files=True)
    question_marks = st.text_input("Enter Marks per Question (comma-separated)", "5, 8, 10")
    
    if key_file and student_files and question_marks:
        key_path = f"key_{int(time.time())}.docx"
        with open(key_path, "wb") as f:
            f.write(key_file.read())
        
        student_paths = []
        for i, student_file in enumerate(student_files):
            student_path = f"student_{i}_{int(time.time())}.docx"
            with open(student_path, "wb") as f:
                f.write(student_file.read())
            student_paths.append(student_path)
        
        marks = [int(m.strip()) for m in question_marks.split(",")]
        if st.button("Evaluate Answers"):
            with st.spinner("Evaluating answers..."):
                output_file = "student_scores.csv"
                process_student_papers(student_paths, key_path, output_file, marks)
                st.success(f"Scores saved to {output_file}")
                with open(output_file, "r") as f:
                    st.text(f.read())  # Display as text (table might need formatting)

# Section 7: Create Google Form
if section == "Create Google Form":
    st.header("Create Google Form with MCQs")
    if not os.path.exists("mcq_questions.txt"):
        st.warning("Please generate MCQs first!")
    else:
        if st.button("Create Form"):
            with st.spinner("Creating Google Form..."):
                edit_url = create_google_form()
                st.success(f"Form created! Edit URL: {edit_url}")
                st.markdown(f"[Edit Form]({edit_url})")

# Section 8: Google Classroom Integration
if section == "Google Classroom Integration":
    st.header("Google Classroom Integration")
    if st.button("List Courses"):
        with st.spinner("Fetching courses..."):
            st.write("Available Courses:")
            list_courses_with_urls()  # Modify this module to return data if needed for Streamlit

# Main entry point
if __name__ == "__main__":
    st.write("Welcome to the Educational Video Tool!")