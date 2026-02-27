from datetime import datetime, timedelta
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

class GoogleCalendarClient:
    def __init__(self, credentials_path, token_path="token.json", calendar_id="primary"):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.calendar_id = calendar_id
        self._service = None

    def _ensure_service(self):
        if self._service is not None:
            return

        try:
            from googleapiclient.discovery import build
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
        except Exception as exc:
            raise RuntimeError(
                "Google Calendar packages are not installed. "
                "Add google-api-python-client, google-auth-httplib2, google-auth-oauthlib."
            ) from exc

        if not self.credentials_path.exists():
            raise RuntimeError("Google credentials file not found.")

        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")

        self._service = build("calendar", "v3", credentials=creds)

    def get_events_for_day(self, date):
        self._ensure_service()

        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)
        time_min = start.isoformat() + "Z"
        time_max = end.isoformat() + "Z"

        events_result = (
            self._service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])
