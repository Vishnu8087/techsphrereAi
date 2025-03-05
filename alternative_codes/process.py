import google.generativeai as genai
import time

# Configure the API key (use environment variables in production)
genai.configure(api_key='your api key')

def upload_and_process_video(video_path):
    """Uploads a video and waits for processing."""
    video_file = genai.upload_file(path=video_path)

    # Wait until processing completes
    while video_file.state.name == "PROCESSING":
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    return video_file.uri

def summarize_video(video_uri):
    """Summarizes the video content using Gemini AI."""
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-001")
    video_file = genai.get_file(video_uri.split('/')[-1])
    
    # Pass the file content directly to the model
    response = model.generate_content([
        "Summarize the video content.",
        video_file
    ])
    
    return response.text

def generate_mcqs(video_uri, num_mcqs, level):
    """Generates MCQs from video content."""
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-001")
    video_file = genai.get_file(video_uri.split('/')[-1])

    prompt = (
        f"Generate {num_mcqs} multiple-choice questions (MCQs) with four options, "
        f"considering difficulty level {level}. At the end, provide the correct answers as a list, "
        "like this: ANSWERS = ['Discriminative and Generative', 'Naive Bayes', 'Logistic Regression', ...]. "
        "Ensure the answers are in full text format, not just option letters, and format options as: a), b), c), d)."
    )

    response = model.generate_content([prompt, video_file])
    return response.text