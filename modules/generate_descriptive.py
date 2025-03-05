import os
import google.generativeai as genai
import re

genai.configure(api_key='your_api_key')

def generate_descriptive_questions(video_obj, num_questions):
    """Generates descriptive questions from video content.

    Args:
        video_obj: A File object from google.generativeai representing the uploaded video.
        num_questions (int): Number of questions to generate.

    Returns:
        str: The generated questions and answers in formatted text.
    """
    model = genai.GenerativeModel("models/gemini-1.5-flash-001")  # Use a supported model
    prompt = (
        f"When given a video and a query, process the video content once with appropriate timecodes and text. "
        f"Ensure all dollar signs are escaped properly in the output. "
        f"You are an expert in creating educational content. Generate a list of {num_questions} questions "
        f"from the video content suitable for an academic setting. For each question: "
        f"Provide a detailed, long-range answer that explains the concept comprehensively and aligns with academic standards. "
        f"Assign marks to each question based on its difficulty level and expected depth of the answer. Ensure: "
        f"Questions are of varying difficulty levels (easy, moderate, challenging). Answers are well-structured, covering all essential details. "
        f"Include marks explicitly for each question. Output Format: "
        f"Qna1) [Question Text]? Ana1) [Detailed Answer] Marks: [Number of Marks] "
        f"Qna2) [Question Text]? Ana2) [Detailed Answer] Marks: [Number of Marks] "
        f"Qna3) [Question Text]? Ana3) [Detailed Answer] Marks: [Number of Marks] "
        f"Number of Questions: {num_questions}"
    )

    response = model.generate_content(
        [prompt, video_obj],
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 4096
        }
    )
    return response.text

def extract_markdown_to_text(markdown_output, question_file, answer_file):
    """Extracts questions and answers from formatted text and writes them to separate files.

    Args:
        markdown_output (str): The text containing questions and answers.
        question_file (str): Path to save the questions.
        answer_file (str): Path to save the answers.
    """
    with open(question_file, 'w', encoding='utf-8') as q_file, open(answer_file, 'w', encoding='utf-8') as a_file:
        # Regex to match Qna/Ana pairs with marks
        qa_pattern = re.findall(
            r'(Qna\d+\)\s*.*?)\?\s*(Ana\d+\)\s*.*?)(?=Marks:|\Z)\s*Marks:\s*(\d+)',
            markdown_output,
            re.DOTALL
        )
        
        if not qa_pattern:
            print("Warning: No Q&A pairs found in the expected format.")
            q_file.write(markdown_output)
            a_file.write("No answers extracted due to format mismatch.")
            return
        
        for question, answer, marks in qa_pattern:
            q_file.write(f"{question.strip()}? (Marks: {marks})\n")
            a_file.write(f"{answer.strip()}\n")
        
        print(f"Extracted {len(qa_pattern)} questions and answers.")