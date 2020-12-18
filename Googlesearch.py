import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def get_gdrive_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    # return Google Drive API service
    return build('drive', 'v3', credentials=creds)

def searchc(searching):
    # service connect the bot to the google drive api
    service = get_gdrive_service()
    # The folder id is supposed to be between '' but I delete it to avoid problems on sharing this folder
    search_result = search(service, query=f"'' in parents and name contains '\"{searching}\"'")
    return search_result

def linkc(searching):
    service = get_gdrive_service()
    # The folder id is supposed to be between '' but I delete it to avoid problems on sharing this folder
    search_result = search(service,
                           query=f"'' in parents and fullText contains '\"{searching}\"'")
    return search_result

def search(service, query):
    # search for the file
    result = []
    page_token = None
    while True:
        response = service.files().list(q=query,
                                        spaces="drive",
                                        fields="nextPageToken, files(id, name, mimeType)",
                                        pageToken=page_token).execute()
        # iterate over filtered files
        for file in response.get("files", []):
            result.append((file["name"], file["id"]))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            # no more files
            break
    return result
