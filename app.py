import os
import json
import re
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def clean_json_string(json_string):
    json_string = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_string)
    try:
        json_obj = json.loads(json_string)
        return json.dumps(json_obj)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error during cleaning: {e}")
        return json_string

def send_message(message, text_to_edit):
    system_prompt = """You are an AI-driven text editor assistant. Your task is to help users edit and improve their text based on their instructions. The user will provide you with the text to be edited and their instructions for editing. Your response should include the edited text, along with any explanations or comments about the changes made."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text to edit:\n{text_to_edit}\n\nInstructions:\n{message}"}
            ],
            functions=[
                {
                    "name": "update_edited_text",
                    "description": "Update the edited text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "edited_text": {
                                "type": "string",
                                "description": "The edited version of the text"
                            }
                        },
                        "required": ["edited_text"]
                    }
                }
            ],
            function_call={"name": "update_edited_text"}
        )
        
        assistant_message = response.choices[0].message
        function_call = assistant_message.function_call

        if function_call and function_call.name == "update_edited_text":
            try:
                cleaned_arguments = clean_json_string(function_call.arguments)
                edited_text = json.loads(cleaned_arguments)["edited_text"]
            except json.JSONDecodeError as json_error:
                print(f"JSON Decode Error: {json_error}")
                print(f"Problematic JSON string: {cleaned_arguments}")
                edited_text = text_to_edit
            
            return edited_text, assistant_message.content
        else:
            return text_to_edit, assistant_message.content
    except Exception as e:
        print(f"An error occurred in send_message: {str(e)}")
        return text_to_edit, f"An error occurred: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/edit', methods=['POST'])
def edit_text():
    data = request.json
    message = data.get('message', '')
    text_to_edit = data.get('text_to_edit', '')
    
    edited_text, response = send_message(message, text_to_edit)
    
    return jsonify({
        'edited_text': edited_text,
        'response': response
    })

if __name__ == '__main__':
    app.run(debug=True)
