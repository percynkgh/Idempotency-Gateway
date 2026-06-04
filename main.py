import time
import hashlib
import json
from fastapi import FastAPI,Header,HTTPException,Response
from pydantic import BaseModel

app =FastAPI()

store={}

class PaymentRequest(BaseModel):
    amount:float
    currency:str
@app.post("/process-payment")
def process_paymwent(
    payment:PaymentRequest,
    response:Response,
    idempotecncy_key:str = Header(...,alias="Idempotency-Key")
):
    body_hash =hashlib.sha256(
        json.dumps(payment.model_dump(),sort_keys=True).encode()
).hexdigest()
    
    if idempotecncy_key in store:
        existing=store[idempotecncy_key]


        if existing["body_hash"] !=body_hash:
            raise HTTPException(
                status_code=422,
                detail="Idempotency key already used for a different request body."
        )

        response.headers["X-Cache-Hit"] ="true"
        return existing["response"]
    time.sleep(2)

    result={
        "status":"success",
        "message":f"Charged {payment.amount} {payment.currency}"
    }

    store[idempotecncy_key]={
        "body_hash":body_hash,
        "response":result
    }

    response.headers["X-Cache=Hit"]="false"
    return result