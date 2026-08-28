"""Firebase Cloud Messaging service for web push notifications."""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app = None


def _init_firebase():
    """Initialize Firebase Admin SDK lazily."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    if not settings.FIREBASE_PROJECT_ID or not settings.FIREBASE_CLIENT_EMAIL or not settings.FIREBASE_PRIVATE_KEY:
        logger.warning(
            "Firebase credentials not configured. Push notifications will not work. "
            "Required: FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY"
        )
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Avoid double-initialization
        if firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
            return _firebase_app

        private_key = settings.FIREBASE_PRIVATE_KEY
        # Handle escaped newlines from env vars
        if "\\n" in private_key:
            private_key = private_key.replace("\\n", "\n")

        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key": private_key,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
        })

        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return _firebase_app
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return None


def is_firebase_configured() -> bool:
    """Check if Firebase is configured."""
    return bool(
        settings.FIREBASE_PROJECT_ID
        and settings.FIREBASE_CLIENT_EMAIL
        and settings.FIREBASE_PRIVATE_KEY
    )


async def send_push_notification(
    token: str,
    title: str,
    body: str,
    url: Optional[str] = None,
    image_url: Optional[str] = None,
) -> dict:
    """Send a push notification to a single FCM token.

    Returns dict with status and any error.
    """
    app = _init_firebase()
    if not app:
        return {"status": "error", "error": "Firebase not configured"}

    try:
        from firebase_admin import messaging

        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url if image_url else None,
        )

        data = {}
        if url:
            data["url"] = url

        message = messaging.Message(
            notification=notification,
            token=token,
            data=data,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    image=image_url if image_url else None,
                    icon="/icon-192.png",
                    badge="/icon-72.png",
                    data={"url": url} if url else None,
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=url if url else None,
                ),
            ),
        )

        response = messaging.send(message)
        logger.info(f"Push notification sent: {response}")
        return {"status": "success", "message_id": response}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send push notification: {error_msg}")
        # Check for invalid token
        if "registration-token" in error_msg.lower() or "invalid" in error_msg.lower():
            return {"status": "invalid_token", "error": error_msg}
        return {"status": "error", "error": error_msg}


async def send_push_to_tokens(
    tokens: list[str],
    title: str,
    body: str,
    url: Optional[str] = None,
    image_url: Optional[str] = None,
) -> dict:
    """Send push notification to multiple FCM tokens.

    Returns dict with success/failure counts and invalid tokens to clean up.
    """
    if not tokens:
        return {"status": "success", "sent": 0, "failed": 0, "invalid_tokens": []}

    app = _init_firebase()
    if not app:
        return {"status": "error", "error": "Firebase not configured", "sent": 0, "failed": 0}

    try:
        from firebase_admin import messaging

        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url if image_url else None,
        )

        data = {}
        if url:
            data["url"] = url

        # Send in batches of 500 (FCM multicast limit)
        sent = 0
        failed = 0
        invalid_tokens = []

        for i in range(0, len(tokens), 500):
            batch = tokens[i:i + 500]
            message = messaging.MulticastMessage(
                notification=notification,
                tokens=batch,
                data=data,
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        image=image_url if image_url else None,
                        icon="/icon-192.png",
                        badge="/icon-72.png",
                        data={"url": url} if url else None,
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=url if url else None,
                    ),
                ),
            )

            response = messaging.send_multicast(message)
            sent += response.success_count
            failed += response.failure_count

            # Collect invalid tokens for cleanup
            for idx, result in enumerate(response.responses):
                if not result.success:
                    error = result.exception
                    if error and (
                        "registration-token" in str(error).lower()
                        or "invalid" in str(error).lower()
                        or "not-found" in str(error).lower()
                    ):
                        invalid_tokens.append(batch[idx])

        logger.info(f"Push sent: {sent} success, {failed} failed, {len(invalid_tokens)} invalid")
        return {
            "status": "success",
            "sent": sent,
            "failed": failed,
            "invalid_tokens": invalid_tokens,
        }
    except Exception as e:
        logger.error(f"Failed to send multicast push: {e}")
        return {"status": "error", "error": str(e), "sent": 0, "failed": len(tokens)}
