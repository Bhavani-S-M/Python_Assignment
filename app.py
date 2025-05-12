from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import boto3
from pathlib import Path
import config

app = FastAPI()

# AWS S3 client setup
s3_client = boto3.client(
    's3',
    region_name=config.AWS_REGION,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
)

bucket_name = config.S3_BUCKET_NAME

# Setup templates and static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        files = response.get('Contents', [])
        file_names = [file['Key'] for file in files]
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "files": file_names, "bucket": bucket_name}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Error listing files: {str(e)}"}
        )

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        s3_client.put_object(Bucket=bucket_name, Key=file.filename, Body=contents)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": f"Upload failed: {str(e)}"}
        )

@app.get("/delete", response_class=HTMLResponse)
async def delete_page(request: Request):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        files = response.get('Contents', [])
        file_names = [file['Key'] for file in files]
        return templates.TemplateResponse(
            "delete.html",
            {"request": request, "files": file_names}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "delete.html",
            {"request": request, "error": f"Error listing files: {str(e)}"}
        )

@app.post("/delete", response_class=HTMLResponse)
async def delete_file(request: Request, file_name: str = Form(...)):
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=file_name)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "delete.html",
            {"request": request, "error": f"Delete failed: {str(e)}"}
        )