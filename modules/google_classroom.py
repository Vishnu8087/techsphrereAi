# modules/google_classroom.py
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

# Load credentials from token1.json
creds_path = os.path.join("credentials", "token1.json")  # Use os.path.join for cross-platform compatibility
creds = Credentials.from_authorized_user_file(creds_path)

# Build the Classroom service
service = build("classroom", "v1", credentials=creds)

def encode_classroom_id(numeric_id):
    """Encodes a numeric Google Classroom ID to its URL-safe Base64 representation.

    Args:
        numeric_id: The numeric ID as a string or integer.

    Returns:
        The Base64 encoded ID as a string.
    """
    # Ensure the input is a string
    id_str = str(numeric_id)
    # Encode the ID as bytes
    id_bytes = id_str.encode('utf-8')
    # Perform Base64 encoding, using URL-safe encoding
    base64_bytes = base64.urlsafe_b64encode(id_bytes)
    # Decode the Base64 to a string and remove padding
    base64_string = base64_bytes.decode('utf-8').rstrip('=')
    return base64_string

def list_courses_with_urls():
    """Fetches and returns a list of courses with their names, IDs, and URLs.

    Returns:
        A list of dictionaries, each containing 'name', 'id', and 'url' for a course.
        Returns an empty list if no courses are found or an error occurs.
    """
    try:
        results = service.courses().list().execute()
        courses = results.get('courses', [])
        course_list = []
        for course in courses:
            base64_id = encode_classroom_id(course['id'])
            course_url = f"https://classroom.google.com/c/{base64_id}"
            course_list.append({
                'name': course['name'],
                'id': course['id'],
                'url': course_url
            })
        return course_list
    except Exception as e:
        print(f"An error occurred: {e}")
        return []  # Return an empty list on errord: