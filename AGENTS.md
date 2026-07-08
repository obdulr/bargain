# Project Notes for AI Agents

## SMS Provider: Telnyx ONLY

**NEVER use Twilio.** Twilio is not used in any project. All SMS, MMS, and messaging functionality uses **Telnyx** exclusively.

- Use the Telnyx API (`https://api.telnyx.com/v2/messages`) for sending SMS
- Env vars: `TELNYX_API_KEY`, `TELNYX_FROM_NUMBER`, `TELNYX_MESSAGING_PROFILE_ID`
- Do not suggest, install, or reference Twilio in any code, config, or documentation

## Package Manager

- Backend (bargain-api): Python with pip, FastAPI
- Frontend (bargain-web): Next.js with npm/pnpm
