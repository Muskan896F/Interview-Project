# REST API Documentation

This document describes the API endpoints provided by the Real Estate Voice Agent backend.

---

### 1. Register Lead
- **Endpoint**: `POST /api/create-lead`
- **Description**: Registers a new customer lead to kickstart outbound workflows.
- **Request Body**:
```json
{
  "name": "Amit Patel",
  "phone": "9876543210",
  "email": "amit@example.com",
  "source": "Website Inquiry"
}
```
- **Response**: `200 OK`
```json
{
  "id": 1,
  "name": "Amit Patel",
  "phone": "9876543210",
  "email": "amit@example.com",
  "source": "Website Inquiry",
  "status": "new"
}
```

---

### 2. Start Conversation
- **Endpoint**: `POST /api/start-conversation`
- **Description**: Starts an outbound dialogue turn, returning the greeting text and audio.
- **Request Body**:
```json
{
  "phone": "9876543210"
}
```
- **Response**: `200 OK`
```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "agent_text": "Hello, hu Patel Group mathi Sarah bolu chhu...",
  "agent_audio_base64": "SUQzBAAAAAAA..."
}
```

---

### 3. Send Message Turn
- **Endpoint**: `POST /api/chat`
- **Description**: Submits typed text or recorded speech to drive the conversation forward.
- **Request Body**:
```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "user_text": "weekend par visit mate booking karvu chhe",
  "user_audio_base64": null
}
```
- **Response**: `200 OK`
```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "agent_text": "Khub saras! To tame site visit Saturday mate book karva mango cho ke Sunday mate?",
  "agent_audio_base64": "SUQzBAAAAAAA...",
  "current_node": "booking",
  "language": "gujarati"
}
```

---

### 4. Fetch Session Summary
- **Endpoint**: `GET /api/summary`
- **Parameters**: `session_id` (string, required)
- **Description**: Retrieves lead scoring metrics and parsed requirements.
- **Response**: `200 OK`
```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "lead_id": 1,
  "lead_score": 85,
  "interested": true,
  "budget": "50 to 60 Lakhs",
  "preferred_location": "Shela",
  "property_type": "3 BHK",
  "purpose": "Self-Use",
  "timeline": "3 months",
  "questions_asked": ["possession kyare malse?"],
  "objections": [],
  "booking_status": "booked",
  "follow_up_status": "not_scheduled",
  "summary_text": "Lead is highly interested. Site visit confirmed for Saturday."
}
```
