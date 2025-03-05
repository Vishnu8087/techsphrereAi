
import json
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# Step 3: Initialize the Gemini model
model = genai.GenerativeModel("gemini-2.0-flash-exp")
num_of = 10
level="easy"
topic="Letter -M"
# Step 4: Define the prompt for MCQ generation
prompt = (
   f"Analyze the provided video and generate{num_of} and {level}with{topic}  strictly follow the topic content four options each "
    "and their correct answers. Output the questions directly as a JSON array, with each question "
    "having 'question', 'options', and 'answer' fields. For example: "
    "[{\"question\": \"What is the capital of France?\", \"options\": [\"Paris\", \"London\", "
    "\"Berlin\", \"Madrid\"], \"answer\": \"Paris\"}, ...]. Ensure the response is a list, "
    "not wrapped in additional objects."
)

# Step 5: Generate MCQs using the Gemini model
response = model.generate_content(
    [prompt, video_file],
    generation_config={"response_mime_type": "application/json"}
)

# Step 6: Parse and validate the JSON response
mcq_data = json.loads(response.text)
if isinstance(mcq_data, list):
    mcq_list = mcq_data
else:
    raise ValueError(f"Expected a list of MCQs, but got {type(mcq_data)}: {mcq_data}")

# Validate each MCQ is a dictionary with required fields
for i, mcq in enumerate(mcq_list):
    if not isinstance(mcq, dict) or not all(key in mcq for key in ['question', 'options', 'answer']):
        raise ValueError(f"MCQ at index {i} is invalid: {mcq}")
    if not isinstance(mcq['options'], list) or len(mcq['options']) != 4:
        raise ValueError(f"MCQ at index {i} must have exactly 4 options: {mcq}")

print("Generated MCQs:", json.dumps(mcq_list, indent=2))

# Step 7: Function to create a Google Form from MCQs
def create_google_form_from_mcqs(mcq_list, form_title="Video Quiz"):
    # Define required scopes for Google Forms API
    SCOPES = ['https://www.googleapis.com/auth/forms.body']
    
    # Authenticate using credentials (ensure token1.json exists with these permissions)
    creds = Credentials.from_authorized_user_file('token1.json', SCOPES)
    service = build('forms', 'v1', credentials=creds)
    
    # Create a new form
    form = {
        "info": {
            "title": form_title,
        }
    }
    form_response = service.forms().create(body=form).execute()
    form_id = form_response['formId']
    
    # Step 8: Prepare batch update requests
    requests = [
        # Enable quiz mode
        {
            "updateSettings": {
                "settings": {
                    "quizSettings": {
                        "isQuiz": True
                    }
                },
                "updateMask": "quizSettings.isQuiz"
            }
        }
    ]
    
    # Step 9: Add MCQs as graded questions
    for i, mcq in enumerate(mcq_list):
        question = mcq['question']
        options = mcq['options']
        answer = mcq['answer']
        
        requests.append({
            "createItem": {
                "item": {
                    "title": question,
                    "questionItem": {
                        "question": {
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [{"value": opt} for opt in options]
                            },
                            "grading": {
                                "pointValue": 1,
                                "correctAnswers": {"answers": [{"value": answer}]}
                            }
                        }
                    }
                },
                "location": {"index": i}
            }
        })
    
    # Step 10: Execute the batch update to apply all changes
    service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
    return form_id

# Step 11: Create the Google Form and output the result
try:
    form_id = create_google_form_from_mcqs(mcq_list)
    print(f"Form created with ID: {form_id}")
    print(f"View your form at: https://docs.google.com/forms/d/{form_id}/edit")
    print("Note: Please manually set the form to limit one response per user in the form settings.")
except Exception as e:
    print(f"Error creating form: {e}")