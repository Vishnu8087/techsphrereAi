
import streamlit as st
import google.generativeai as genai
import subprocess
import os
import time
from modules.record import list_devices
from modules.process_video import upload_and_process_video, summarize_video, generate_mcqs, clear_mcq_cache
from modules.generate_descriptive import generate_descriptive_questions, extract_markdown_to_text
from modules.validate_answers import process_student_papers
from modules.pgoogle_form import create_google_form
from modules.google_classroom import list_courses_with_urls

# Configure the API key for Google Generative AI
genai.configure(api_key='your api  key')  
# Streamlit App Configuration
st.set_page_config(page_title="Educational Video Tool", layout="wide")
st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to", [
    "Record Video",
    "upload_video",
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
    st.write(f"Playing {file_path} in Streamlit:")
    st.video(file_path)

# Section 1: Record Video
if section == "Record Video":
    st.header("Record Video")
    video_devices, audio_devices = list_devices()
    if not video_devices or not audio_devices:
        st.error("No devices found!")
    else:
        st.subheader("Select Devices")
        video_device = st.selectbox("Video Device", video_devices)
        audio_device = st.selectbox("Audio Device", audio_devices)
        output_file = "output.mkv"
        if "recording_process" not in st.session_state:
            st.session_state.recording_process = None
            st.session_state.is_recording = False

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Recording", disabled=st.session_state.is_recording):
                if os.path.exists(output_file):
                    os.remove(output_file)
                process = subprocess.Popen([
                    "ffmpeg", "-f", "dshow", "-rtbufsize", "100M",
                    "-i", f"video={video_device}:audio={audio_device}",
                    "-pix_fmt", "yuv420p", "-s", "640x480", "-r", "20",
                    "-c:v", "libx264", "-preset", "ultrafast",  "-b:v", "300k",
                    "-c:a", "aac", "-b:a", "75k", "-map", "0:v", "-map", "0:a",
                    output_file
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                st.session_state.recording_process = process
                st.session_state.is_recording = True
                st.success("Recording started.")

        with col2:
            if st.button("Stop Recording", disabled=not st.session_state.is_recording):
                if st.session_state.recording_process:
                    try:
                        st.session_state.recording_process.terminate()
                        st.session_state.recording_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        st.session_state.recording_process.kill()
                        st.warning("Recording forcefully stopped.")
                    st.session_state.is_recording = False
                    st.session_state.recording_process = None
                    time.sleep(1)
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                        st.success(f"Recording saved as {output_file}")
                    else:
                        st.error("Recording file may be empty.")
                else:
                    st.error("No recording to stop!")

        if os.path.exists(output_file) and not st.session_state.is_recording:
            if st.button("Play Recording"):
                play_recording(output_file)

# Section 2: Process Video
if section == "upload_video":
    st.header("upload_video")
    video_file = st.file_uploader("Upload Video File", type=["mkv"])
    if video_file:
        video_path = f"uploaded_video_{int(time.time())}.mkv"
        with open(video_path, "wb") as f:
            f.write(video_file.read())
        st.success(f"Video uploaded: {video_path}")
        
        with st.spinner("Processing video..."):
            video_obj = genai.upload_file(path=video_path)
            while video_obj.state.name == "PROCESSING":
                time.sleep(10)
                video_obj = genai.get_file(video_obj.name)
            st.session_state["video_obj"] = video_obj
            st.write(f"Video processed: {video_obj.uri}")

# Section 3: Summarize Video
if section == "Summarize Video":
    st.header("Summarize Video")
    if "video_obj" not in st.session_state:
        st.warning("Please process a video first!")
    else:
        if st.button("Generate Summary"):
            with st.spinner("Generating summary..."):
                summary = summarize_video(st.session_state["video_obj"].uri)
                st.markdown(summary)

# Section 4: Generate MCQs
if section == "Generate MCQs":
    st.header("Generate Multiple Choice Questions")
    if "video_obj" not in st.session_state:
        st.warning("Please process a video first!")
    else:
        num_mcqs = st.number_input("Number of MCQs", min_value=1, max_value=50, value=20)
        difficulty = st.selectbox("Difficulty Level", ["easy", "medium", "hard"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate MCQs"):
                with st.spinner("Generating MCQs..."):
                    mcq_text = generate_mcqs(st.session_state["video_obj"].uri, num_mcqs, difficulty)
                    st.session_state["mcq_text"] = mcq_text  # Store for display
                    with open("mcq_questions.txt", "w", encoding="utf-8") as f:
                        f.write(mcq_text)
                    st.success("MCQs generated and saved to mcq_questions.txt")
        
        with col2:
            if st.button("Delete Cache"):
                clear_mcq_cache()
                st.success("MCQ cache deleted. Next generation will fetch fresh questions.")
        
        # Display the MCQs if they exist
        if "mcq_text" in st.session_state:
            st.markdown("### Generated MCQs")
            st.markdown(st.session_state["mcq_text"])

# Section 5: Generate Descriptive Questions
if section == "Generate Descriptive Questions":
    st.header("Generate Descriptive Questions")
    if "video_obj" not in st.session_state:
        st.warning("Please process a video first!")
    else:
        num_questions = st.number_input("Number of Questions", min_value=1, max_value=10, value=3)
        if st.button("Generate Questions"):
            with st.spinner("Generating questions..."):
                descriptive_text = generate_descriptive_questions(st.session_state["video_obj"], num_questions)
                st.markdown(descriptive_text)
                extract_markdown_to_text(descriptive_text, "questions.txt", "answers.txt")
                st.success("Saved to questions.txt and answers.txt")

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
                    st.text(f.read())

# Section 7: Create Google Form
if section == "Create Google Form":
    st.header("Create Google Form with MCQs")
    if not os.path.exists("mcq_questions.txt"):
        st.warning("Please generate MCQs first!")
    else:
        if st.button("Create Form"):
            with st.spinner("Creating Google Form..."):
                result = create_google_form()
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Form created successfully!")
                    st.markdown(f"**Form URL:** [{result['form_url']}]({result['form_url']})")
                    st.markdown(f"**Published URL:** [{result['published_url']}]({result['published_url']})")
                    st.markdown(f"**Edit URL:** [{result['edit_url']}]({result['edit_url']})")

# Section 8: Google Classroom Integration
if section == "Google Classroom Integration":
    st.header("Google Classroom Integration")
    if st.button("List Courses"):
        with st.spinner("Fetching courses..."):
            try:
                courses = list_courses_with_urls()
                if courses:
                    st.subheader("Available Courses")
                    for course in courses:
                        st.markdown(f"**Name:** {course['name']}  \n**ID:** {course['id']}  \n**URL:** [{course['url']}]({course['url']})")
                else:
                    st.info("No courses found.")
            except Exception as e:
                st.error(f"An error occurred while fetching courses: {e}")

# Main entry point
if __name__ == "__main__":
    st.title("Educational Video Tool")
    st.write("Welcome to the Educational Video Tool! Use the sidebar to navigate.")