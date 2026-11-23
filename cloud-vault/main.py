import os
import boto3
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CloudVault - Cloud Computing Project")

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION,
)

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CloudVault - S3 File Manager</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .box { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
            button { background: #0070f3; color: white; border: none; padding: 10px 16px; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0051b3; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>CloudVault: AWS S3 Document Uploader</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required />
                <br><br>
                <button type="submit">Upload to AWS S3</button>
            </form>
            <hr>
            <p><a href="/files">View Uploaded Files (JSON)</a> | <a href="/docs">API Docs</a></p>
        </div>
    </body>
    </html>
    """

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        return {"status": "success", "filename": file.filename, "bucket": S3_BUCKET}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
def list_files():
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        files = [obj["Key"] for obj in response.get("Contents", [])]
        return {"bucket": S3_BUCKET, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))