# server/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import openai
from jira import JIRA
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../.env")

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost:3000",  # Frontend URL
    "http://localhost",        # Additional if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")  # If using Azure OpenAI

# Initialize JIRA Client
jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY
if OPENAI_ENDPOINT:
    openai.api_base = OPENAI_ENDPOINT

class SummarizeRequest(BaseModel):
    text: str

@app.get("/api/issues")
def get_issues():
    try:
        issues = jira.search_issues('project=YOURPROJECT', maxResults=10)
        issue_list = [
            {
                "key": issue.key,
                "title": issue.fields.summary,
                "description": issue.fields.description or "No description provided.",
            }
            for issue in issues
        ]
        return issue_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summarize")
def summarize(request: SummarizeRequest):
    try:
        response = openai.Completion.create(
            engine="davinci",  # Replace with your model if using Azure OpenAI
            prompt=f"Summarize the following JIRA ticket:\n\n{request.text}",
            max_tokens=150,
            temperature=0.5,
        )
        summary = response.choices[0].text.strip()
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
