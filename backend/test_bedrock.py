import boto3
import os
import sys
from dotenv import load_dotenv

load_dotenv("c:/New folder (2)/repo/backend/.env")

key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
region = os.getenv("AWS_REGION", "ap-south-1")

print(f"Region : {region}")
print(f"Key ID : {key_id[:8]}...{key_id[-4:]}")

try:
    client = boto3.client(
        "bedrock",
        region_name=region,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
    )
    models = client.list_foundation_models(byOutputModality="TEXT")
    all_models = [
        m["modelId"] for m in models["modelSummaries"]
        if any(x in m["modelId"].lower() for x in ["llama", "mistral", "claude", "titan"])
    ]
    print(f"Available models: {all_models}")
except Exception as e:
    print(f"Connection error: {e}")
    sys.exit(1)

# Test model access
try:
    runtime = boto3.client(
        "bedrock-runtime",
        region_name=region,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
    )
    import json
    body = json.dumps({
        "prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\nSay hello in one sentence.<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n",
        "max_gen_len": 50,
        "temperature": 0.1,
    })
    response = runtime.invoke_model(
        modelId="meta.llama3-8b-instruct-v1:0",
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    text = result.get("generation", "").strip()
    print(f"Model test OK: {text}")
except Exception as e:
    print(f"Model invoke error: {e}")
    print("You may need to enable model access in AWS Console -> Bedrock -> Model Access")
