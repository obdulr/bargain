import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError

from app.core.config import settings


_firebase_app = None


def get_firebase_app():
    """Initialize and return the Firebase Admin app if credentials are available."""
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    cred = None

    if settings.FIREBASE_CREDENTIALS_JSON:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_JSON)
    elif settings.FIREBASE_CREDENTIALS_PATH:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

    if cred is None:
        return None

    try:
        _firebase_app = firebase_admin.initialize_app(cred)
    except ValueError:
        # App already initialized
        _firebase_app = firebase_admin.get_app()
    except FirebaseError:
        return None

    return _firebase_app


def send_push_notification(token: str, title: str, body: str, data: dict | None = None):
    """Send a push notification via Firebase Cloud Messaging."""
    app = get_firebase_app()
    if app is None:
        return None

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    return messaging.send(message, app=app)
