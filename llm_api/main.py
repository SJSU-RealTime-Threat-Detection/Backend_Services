from openai import OpenAI
from google import genai
from google.genai import types
import json
import os
import time
import uuid
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import PyMongoError
from datetime import datetime
import uuid
import requests

load_dotenv()

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

GENERATION_CONFIG = {
    "temperature": 0.3,
    "max_output_tokens": 1500,
}

SYSTEM_INSTRUCTION = """
You are a seasoned cybersecurity analyst specializing in Apache server logs.
Your job is to perform structured, detailed, and professional analysis reports.
Always be precise, prioritize critical findings, and offer practical recommendations.
"""

def build_prompt(anomalous_logs):
    """Builds the structured analysis prompt."""
    return f"""
{SYSTEM_INSTRUCTION}

You are a senior cybersecurity analyst specializing in web server (Apache) log analysis.

You have been provided a batch of anomalous logs identified by an anomaly detection system.

Please generate a detailed and structured Security Threat Analysis Report following this format.

Important:
- Output must be in plaintext.
- Do NOT use markdown, HTML, or any special formatting.
- Only use plain text symbols such as equal signs, dashes, and spaces for organization.
- Prioritize clarity, professionalism, and actionable insights.

Format:

===============================
Security Threat Analysis Report
===============================

Executive Summary
------------------
- A brief overview of key anomalies detected (2-5 sentences).
- Highlight critical threats and overall risk posture.

Incident Metadata
------------------
For each anomaly, provide a structured plain text list with these fields:
Service: [Service Name]
Severity: [High/Medium/Low]
Model Trigger: [Detection Event Name]
Confidence Score: [Percentage]
Detection Time: [UTC Timestamp]

Indicators of Compromise (IOCs)
-------------------------------
- List all suspicious IP addresses and any suspicious URLs encountered.

Timeline of Events
-------------------
- List anomalies chronologically by detection time, summarizing the action.

Anomaly Summary
----------------
- Bullet points summarizing each anomaly in 1-2 sentences.

Critical Findings
------------------
- For high and critical-risk findings:
  - Description: [Short description of the suspicious behavior]
  - Potential Attack Type: [e.g., Reconnaissance, Exploitation]
  - Threat Classification: [Classification]
  - Risk Score: [Low/Medium/High/Critical]

Other Findings
--------------
- For medium and low-risk findings, similar to Critical Findings but separated.

Immediate Recommended Actions
-------------------------------
- Numbered list of direct actions to immediately contain or mitigate threats.

Long-Term Mitigation Strategies
--------------------------------
- Numbered or bullet list of strategies to improve long-term security posture.

Threat Attribution
-------------------
- Summarize if the patterns resemble known attack types or TTPs (Tactics, Techniques, and Procedures).
- Clarify if attribution to a specific actor is possible or not.

Confidence Score Interpretation
--------------------------------
- Explain how to interpret the confidence scores provided.

Additional Observations
------------------------
- Trends, repeated patterns, or other relevant security insights.

Formatting Rules:
------------------
- The main title must be surrounded with equal signs (=).
- Section headers must be underlined with dashes (-).
- Lists must use plain text bullets (-) or numbers (1., 2., 3.).
- Keep the report clear, professional, and detailed without using any special formatting or links.

Here are the anomalous logs:

{json.dumps(anomalous_logs, indent=2)}
"""

@app.route('/hello', methods=['GET'])
def hello_world():
    """Simple hello world endpoint."""
    return jsonify({"message": "Hello, World!"}), 200

@app.route('/analyze', methods=['POST'])
def analyze_logs():
    """
    Endpoint to analyze logs and return a structured report.
    """
    try:
        # Validate request body
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        anomalous_logs = request.json.get('anomalous_logs', None)
        if not anomalous_logs:
            return jsonify({"error": "No anomalous logs provided"}), 400

        # Start timing the request
        start_time = time.time()

        # Build and send prompt
        try:
            prompt = build_prompt(anomalous_logs)
            response = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            print("Prompt sent successfully.")
        except Exception as e:
            app.logger.error(f"OpenAI API error: {str(e)}")
            return jsonify({"error": "Failed to generate analysis", "details": str(e)}), 500

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Extract report from response
        try:
            report = response.output[0].content[0].text
        except (AttributeError, IndexError) as e:
            app.logger.error(f"Error parsing OpenAI response: {str(e)}")
            return jsonify({"error": "Failed to parse API response"}), 500

        print("==========================")
        print("Report generated successfully.")
        print(report)
        print("==========================")

        # Make API Call to add data to and Send Notification
        #TODO: Add the logic to send the report to a notification service or database
        
        r = save_and_notify({
            "llm_response": report,
            "logs": anomalous_logs,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "model": "gpt-4.1-mini",
            "response_time_seconds": round(elapsed_time, 2),
            "response_time_ms": round(elapsed_time * 1000, 2)
        })
        print(r)

        return jsonify({
            "save_and_notify": r,
            "llm_response": report,
            "logs": anomalous_logs,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "model": "gpt-4.1-mini",
            "response_time_seconds": round(elapsed_time, 2),
            "response_time_ms": round(elapsed_time * 1000, 2)
        }), 200

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/gemini', methods=['POST'])
def analyze_logs_gemini():
    try:
        anomalous_logs = request.json.get('anomalous_logs')
        if not anomalous_logs:
            return jsonify({"error": "No anomalous logs provided."}), 400

        prompt = build_prompt(anomalous_logs)

        start_time = time.time()

        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            ),
        )

        elapsed_time = time.time() - start_time

        report = response.text

        r = save_and_notify({
            "llm_response": report,
            "logs_analyzed": len(anomalous_logs),
            "logs": anomalous_logs,
            "model_used": "gemini-2.0-flash",
            "response_time_seconds": round(elapsed_time, 2),
            "response_time_ms": round(elapsed_time * 1000, 2)
        })
        print(r)
        return jsonify({
            "save_and_notify": r,
            "llm_response": report,
            "logs_analyzed": len(anomalous_logs),
            "logs": anomalous_logs,
            "model_used": "gemini-2.0-flash",
            "response_time_seconds": round(elapsed_time, 2),
            "response_time_ms": round(elapsed_time * 1000, 2)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

def save_and_notify(data):
    try:
        url = os.getenv("NOTIFICATION_URL")
        if not url:
            raise ValueError("NOTIFICATION_URL environment variable not set.")
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}



@app.route('/testing', methods=['POST'])
def testing():
    response = save_and_notify(request.json)
    print(response)
    if response.get("error"):
        return jsonify({"error": response["error"]}), 500
    return jsonify(response), 200

# @app.route('/add_to_db', methods=['GET'])
# def add_data_to_db():
#     url = "https://jsonplaceholder.typicode.com/posts/1"  # Example API (GET)
#     response = make_api_request(url)

#     if response.get("error"):
#         return jsonify({"error": response["error"]}), 500
#     return jsonify(response), 200

def make_api_request(url, method='GET', headers=None, data=None):
    """
    Makes an API request to the specified URL.

    Args:
        url (str): The URL to make the request to.
        method (str): The HTTP method to use (default is 'GET').
        headers (dict): Optional headers to include in the request.
        data (dict or str): Optional data to send with the request (for POST/PUT).

    Returns:
        dict: A dictionary containing the response data or an error message.
    """

    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.route('/ping', methods=['GET'])
def ping():
    """Ping endpoint to check if the service is running."""
    return jsonify({
        "status": "running",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "OpenAI_API_Key": OPENAI_API_KEY is not None,
    }), 200


if __name__ == '__main__':
    app.run(debug=True)