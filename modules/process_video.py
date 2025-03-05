# modules/process_video.py

import os
import google.generativeai as genai
import time

genai.configure(api_key='your api key' )

# Manual cache dictionary
cache = {}

def upload_and_process_video(video_path):
    """Uploads a video file and returns its URI.

    Args:
        video_path (str): Path to the video file on disk.

    Returns:
        str: The URI of the uploaded video.
    """
    video_file = genai.upload_file(path=video_path)
    while video_file.state.name == "PROCESSING":
        time.sleep(10)
        video_file = genai.get_file(video_file.name)
    return video_file.uri

def cache_content(key, content, ttl=3600):
    """Stores content in the manual cache with a time-to-live (TTL).

    Args:
        key (str): Unique identifier for the cached content.
        content (str): The content to cache.
        ttl (int): Time-to-live in seconds (default: 3600, i.e., 1 hour).
    """
    cache[key] = {
        "content": content,
        "timestamp": time.time(),
        "ttl": ttl
    }
    print(f"Cached content for key: {key} (TTL: {ttl} seconds)")

def get_cached_content(key):
    """Retrieves content from the cache if it’s still valid.

    Args:
        key (str): The cache key to look up.

    Returns:
        str or None: The cached content if valid, otherwise None.
    """
    if key in cache:
        entry = cache[key]
        if time.time() - entry["timestamp"] <= entry["ttl"]:
            print(f"Fetching from cache: {key}")
            return entry["content"]
        else:
            print(f"Cache expired for: {key}")
            del cache[key]
    return None

def clear_mcq_cache():
    """Clears all MCQ-related entries from the cache."""
    keys_to_delete = [key for key in cache.keys() if key.startswith("mcqs_")]
    for key in keys_to_delete:
        del cache[key]
    print("MCQ cache cleared.")

def summarize_video(video_uri):
    """Generates a summary of the video content, using manual caching.

    Args:
        video_uri (str): URI of the video to summarize.

    Returns:
        str: The summarized content.
    """
    cache_key = f"summary_{video_uri}"
    cached_summary = get_cached_content(cache_key)
    if cached_summary:
        return cached_summary
    
    model = genai.GenerativeModel("models/gemini-1.5-flash-001")
    video_file = genai.get_file(video_uri.split('/')[-1])
    response = model.generate_content(
        ["Summarize the video content.", video_file],
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 500
        }
    )
    summary = response.text
    cache_content(cache_key, summary)
    return summary

def generate_mcqs(video_uri, num_mcqs, level):
    """Generates multiple-choice questions (MCQs) from video content, with manual caching.

    Args:
        video_uri (str): URI of the video to generate MCQs from.
        num_mcqs (int): Number of MCQs to generate.
        level (str): Difficulty level ("easy", "medium", "hard").

    Returns:
        str: The generated MCQs with answers.
    """
    cache_key = f"mcqs_{video_uri}_{num_mcqs}_{level}"
    cached_mcqs = get_cached_content(cache_key)
    if cached_mcqs:
        return cached_mcqs
    
    model = genai.GenerativeModel("models/gemini-1.5-flash-001")
    video_file = genai.get_file(video_uri.split('/')[-1])
    prompt = (
        f"Generate {num_mcqs} multiple-choice questions (MCQs) with four options, "
        f"considering difficulty level {level}. At the end, provide the correct answers "
        "as a direct list of full answer texts, like this:generate title before question generated "
        "ANSWERS = ['Discriminative and Generative', 'Naive Bayes', 'Logistic Regression', ...]. "
        "Ensure each question has exactly 4 options, answers are in full text format (not just letters) but options very short, "
        "and options are formatted as a), b), c), d). Generate unique questions each time."
    )
    response = model.generate_content(
        [prompt, video_file],
        generation_config={
            "temperature": 1.0,
            "max_output_tokens": 4096
        }
    )
    mcq_text = response.text
    cache_content(cache_key, mcq_text)
    return mcq_text