from fastapi import FastAPI, Request
from azure.communication.callautomation import (
    CallAutomationClient,
    TextSource,
    RecognizeInputType
)

app = FastAPI()

# =========================================
# CONFIGURATION
# =========================================

ACS_CONNECTION_STRING = "YOUR_AZURE_CONNECTION_STRING"
CALLBACK_URI = "https://your-ngrok-url.ngrok-free.app"

client = CallAutomationClient.from_connection_string(
    ACS_CONNECTION_STRING
)

# =========================================
# STEP 1 → INCOMING CALL
# =========================================

@app.post("/acs/incoming-call")
async def incoming_call(request: Request):
    event = await request.json()

    incoming_call_context = event["data"]["incomingCallContext"]

    # STEP 2 → ANSWER CALL
    answer = client.answer_call(
        incoming_call_context=incoming_call_context,
        callback_url=f"{CALLBACK_URI}/acs/callbacks"
    )

    call_id = answer.call_connection_id
    call_connection = client.get_call_connection(call_id)

    # STEP 3 → PLAY WELCOME PROMPT + COLLECT DTMF
    welcome_prompt = TextSource(
        text=(
            "Welcome to IRCTC Railway Booking System. "
            "Press 1 for Ticket Booking. "
            "Press 2 for PNR Status. "
            "Press 3 for Train Schedule."
        ),
        voice_name="en-IN-NeerjaNeural"
    )

    call_connection.start_recognizing_media(
        input_type=RecognizeInputType.DTMF,
        play_prompt=welcome_prompt,
        max_tones_to_collect=1,
        interrupt_prompt=True,
        operation_context="irctc_main_menu"
    )

    return {"message": "IRCTC IVR started"}

# =========================================
# STEP 4 → CALLBACK HANDLER
# =========================================

@app.post("/acs/callbacks")
async def callbacks(request: Request):
    events = await request.json()

    for event in events:
        if event["type"] == "Microsoft.Communication.RecognizeCompleted":

            call_id = event["data"]["callConnectionId"]
            tones = event["data"]["recognizeResult"]["dtmfResult"]["tones"]

            digit = tones[0] if tones else None

            call_connection = client.get_call_connection(call_id)

            # PROCESS DIGIT
            if digit == "one":
                message = (
                    "You selected Ticket Booking. "
                    "Please visit our website www dot irctc dot co dot in "
                    "to complete your booking."
                )

            elif digit == "two":
                message = (
                    "You selected PNR Status. "
                    "Please enter your PNR number on the IRCTC website."
                )

            elif digit == "three":
                message = (
                    "You selected Train Schedule. "
                    "Please check train timings on the IRCTC portal."
                )

            else:
                message = "Invalid selection. Please try again later."

            response_prompt = TextSource(
                text=message,
                voice_name="en-IN-NeerjaNeural"
            )

            call_connection.play_media(play_source=response_prompt)
            call_connection.hang_up(is_for_everyone=True)

    return {"message": "Processed Successfully"}