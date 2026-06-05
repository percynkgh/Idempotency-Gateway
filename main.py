import time
import hashlib
import json
import threading
from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

app = FastAPI()

store = {}
locks = {}
locks_lock = threading.Lock()

class PaymentRequest(BaseModel):
    amount: float
    currency: str

@app.post("/process-payment")
def process_payment(
    payment: PaymentRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    # Step 1: Fingerprint the request body
    body_hash = hashlib.sha256(
        json.dumps(payment.model_dump(), sort_keys=True).encode()
    ).hexdigest()

    # Step 2: Get or create a lock for this specific key
    with locks_lock:
        if idempotency_key not in locks:
            locks[idempotency_key] = threading.Lock()
        key_lock = locks[idempotency_key]

    # Step 3: Only one request per key can enter at a time
    with key_lock:

        # Step 4: Check TTL - delete if older than 24 hours
        if idempotency_key in store:
            existing = store[idempotency_key]
            age = time.time() - existing["created_at"]
            if age > 86400:
                del store[idempotency_key]

        # Step 5: Check store again after TTL check
        if idempotency_key in store:
            existing = store[idempotency_key]

            # Different body - reject
            if existing["body_hash"] != body_hash:
                raise HTTPException(
                    status_code=422,
                    detail="Idempotency key already used for a different request body."
                )

            # Same body - return cached response
            response.headers["X-Cache-Hit"] = "true"
            return existing["response"]

        # Step 6: New key - process the payment
        time.sleep(2)

        result = {
            "status": "success",
            "message": f"Charged {payment.amount} {payment.currency}"
        }

        # Step 7: Save to store with timestamp
        store[idempotency_key] = {
            "body_hash": body_hash,
            "response": result,
            "created_at": time.time()
        }

        response.headers["X-Cache-Hit"] = "false"
        return result