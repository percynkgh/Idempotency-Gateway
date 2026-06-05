import threading
import requests

url = "http://127.0.0.1:8000/process-payment"
headers = {"Idempotency-Key": "race-test-001"}
body = {"amount": 300, "currency": "GHS"}

results = []

def send_request():
    response = requests.post(url, json=body, headers=headers)
    results.append(response.json())

# Create two threads - they will fire at the same time
thread1 = threading.Thread(target=send_request)
thread2 = threading.Thread(target=send_request)

# Start both simultaneously
thread1.start()
thread2.start()

# Wait for both to finish
thread1.join()
thread2.join()

# Check results
print("Request 1 result:", results[0])
print("Request 2 result:", results[1])

if results[0] == results[1]:
    print("\n RACE CONDITION HANDLED - Both got the same response!")
else:
    print("\n RACE CONDITION FAILED - Different responses returned!")