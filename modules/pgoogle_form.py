import re
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def create_google_form():
    # Define OAuth2 scopes
    SCOPES = [
        "https://www.googleapis.com/auth/forms.body",
        "https://www.googleapis.com/auth/forms.responses.readonly",
        "https://www.googleapis.com/auth/drive.file"
    ]

    # Load credentials and build the Forms API service
    try:
        creds = Credentials.from_authorized_user_file(r"credentials\token1.json", SCOPES)
        service = build("forms", "v1", credentials=creds)
    except Exception as e:
        return {"error": f"Failed to initialize Google Forms service: {e}"}

    # File path to MCQ text file
    file_path = r"D:\tech_sphrereAi\mcq_questions.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            mcq_text = file.read()
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        return {"error": f"Error reading file: {e}"}

    # Preprocess the MCQ text
    def preprocess_text(text):
        # Remove unwanted headers
        text = re.sub(r"^Content of mcq_questions\.txt:.*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^##\s*Multiple Choice Questions.*", "", text, flags=re.MULTILINE)
        # Split into non-empty lines
        return "\n".join(line.strip() for line in text.split("\n") if line.strip())

    mcq_text = preprocess_text(mcq_text)

    # Parse questions, options, and answers
    def parse_mcq_content(text):
        questions = []
        answers = []
        current_question = None
        options = []
        parsing_answers = False
        raw_answers = []

        for line in text.split("\n"):
            # Match question (e.g., **1. Question text**)
            if re.match(r"^\*\*(\d+)\.\s+(.+?)\*\*$", line):
                if current_question and options:
                    questions.append({"question": current_question, "options": options})
                match = re.match(r"^\*\*(\d+)\.\s+(.+?)\*\*$", line)
                current_question = match.group(2).strip()
                options = []
            # Match option (e.g., a) Option text)
            elif re.match(r"^[a-d]\)\s+(.+)$", line, re.IGNORECASE):
                match = re.match(r"^([a-d])\)\s+(.+)$", line, re.IGNORECASE)
                if match:
                    options.append({
                        "letter": match.group(1).upper(),
                        "value": match.group(2).strip()
                    })
            # Start parsing answers section
            elif line.strip().startswith("## ANSWERS = ["):
                parsing_answers = True
                raw_answers = []
            # End parsing answers section
            elif line.strip() == "]" and parsing_answers:
                parsing_answers = False
                answers = [ans.strip("', ") for ans in raw_answers if ans.strip()]
            # Collect raw answer lines
            elif parsing_answers:
                raw_answers.append(line.strip())

        # Append the last question
        if current_question and options:
            questions.append({"question": current_question, "options": options})

        return questions, answers

    questions, answers = parse_mcq_content(mcq_text)

    # Validate parsing
    if not questions:
        return {"error": "No questions parsed from the file"}

    # Create the Google Form
    try:
        # Create form metadata
        form_metadata = {
            "info": {
                "title": "Automated MCQ Quiz",
                "documentTitle": "Automated MCQ Quiz"
            }
        }
        form = service.forms().create(body=form_metadata).execute()
        form_id = form["formId"]

        # Build batch request
        batch_requests = [
            {
                "updateSettings": {
                    "settings": {"quizSettings": {"isQuiz": True}},
                    "updateMask": "quizSettings.isQuiz"
                }
            }
        ]

        # Add questions and grading
        for i, question in enumerate(questions):
            question_item = {
                "createItem": {
                    "item": {
                        "title": question["question"],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value": opt["value"]} for opt in question["options"]]
                                }
                            }
                        }
                    },
                    "location": {"index": i}
                }
            }

            # Add grading if answer exists
            if i < len(answers):
                correct_answer = answers[i]
                matching_option = next((opt for opt in question["options"] if opt["value"] == correct_answer), None)
                if matching_option:
                    question_item["createItem"]["item"]["questionItem"]["question"]["grading"] = {
                        "pointValue": 1,
                        "correctAnswers": {"answers": [{"value": matching_option["value"]}]}
                    }

            batch_requests.append(question_item)

        # Execute batch request
        service.forms().batchUpdate(formId=form_id, body={"requests": batch_requests}).execute()

        # Generate URLs
        form_url = f"https://docs.google.com/forms/d/{form_id}"
        published_url = f"https://docs.google.com/forms/d/e/{form_id}/viewform"
        edit_url = f"https://docs.google.com/forms/d/{form_id}/edit"

        return {
            "form_url": form_url,
            "published_url": published_url,
            "edit_url": edit_url
        }

    except Exception as e:
        return {"error": f"Failed to create Google Form: {e}"}

# Example usage
if __name__ == "__main__":
    result = create_google_form()
    print(json.dumps(result, indent=2))