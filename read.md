Educational Video Tool
A Streamlit-based application designed for educators to record, process, and analyze educational videos. This tool leverages the Google Generative AI API to generate summaries, create multiple-choice and descriptive questions, evaluate student answers, and integrate with Google services such as Google Forms and Google Classroom.  evaluate descriptve(text_content) and mcqs 
  
Features
Record Video: Record videos using your device's camera and microphone (Windows only) before run  you can install ffmpeg in your devices record.py module available the code  file is the record the video 
Upload Video: Upload and process video files in MKV format. google gen.ai upload method to upload files 
Summarize Video: Generate a summary of the video content using Google Generative AI. there is an  
Generate MCQs: Create multiple-choice questions (MCQs) based on the video content with customizable quantity and difficulty. upload video , summarize video , generate mcqs  the code is available in the process_video.py  in module directory in the generate mcq,summariaze module we can use context catching the question are repeated in same topic there is an alternative which does not contain context catching the code is available in alternative_codes processs.Py code both are working 
Generate Descriptive Questions: Generate descriptive questions from the video content with answers saved separately.
Evaluate Answers: Evaluate student answers (in DOCX format) against a key answer file and  key and and student answwers can available in same format and answer should in text format and all the answer should follow ssome stands the answer pass like this data module  fear_free _validations in that type