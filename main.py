from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import boto3
import os
from botocore.exceptions import ClientError
import config  # Import your config.py file

app = FastAPI()

# Use credentials from config.py to create a session
session = boto3.Session(
    aws_access_key_id=config.AWS_ACCESS_KEY,
    aws_secret_access_key=config.AWS_SECRET_KEY,
    region_name=config.AWS_REGION
)
s3 = session.client("s3")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------------------- Home Page ----------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    buckets = s3.list_buckets().get("Buckets", [])
    return templates.TemplateResponse("index.html", {"request": request, "buckets": buckets})

# ---------------------- List Objects ----------------------
@app.post("/list_objects")
async def list_objects(request: Request, bucket_name: str = Form(...)):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        contents = response.get("Contents", [])
        return templates.TemplateResponse("index.html", {
            "request": request, "buckets": s3.list_buckets().get("Buckets", []),
            "selected_bucket": bucket_name, "contents": contents
        })
    except ClientError as e:
        return {"error": str(e)}

# ---------------------- Create Bucket ----------------------
@app.post("/create_bucket")
async def create_bucket(request: Request, bucket_name: str = Form(...)):
    try:
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": "eu-north-1"})
    except Exception as e:
        return {"error": f"Error creating bucket: {str(e)}"}
    
    # Refresh bucket list and show the selected bucket
    buckets = s3.list_buckets().get("Buckets", [])
    return templates.TemplateResponse("index.html", {"request": request, "buckets": buckets})

# ---------------------- Delete Bucket ----------------------
@app.post("/delete_bucket")
async def delete_bucket(request: Request, bucket_name: str = Form(...)):
    try:
        s3.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        return {"error": f"Error deleting bucket: {str(e)}"}

    # Refresh bucket list
    buckets = s3.list_buckets().get("Buckets", [])
    return templates.TemplateResponse("index.html", {"request": request, "buckets": buckets})

# ---------------------- Create Folder ----------------------
@app.post("/create_folder")
async def create_folder(request: Request, bucket_name: str = Form(...), folder_name: str = Form(...)):
    try:
        # Create the folder by uploading an empty object with the folder name
        s3.put_object(Bucket=bucket_name, Key=f"{folder_name}/")
        
        # List objects in the bucket after creating the folder
        response = s3.list_objects_v2(Bucket=bucket_name)
        contents = response.get("Contents", [])
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "buckets": s3.list_buckets().get("Buckets", []),
            "selected_bucket": bucket_name,
            "contents": contents
        })
    except Exception as e:
        return {"error": f"Error creating folder: {str(e)}"}

# ---------------------- Upload File ----------------------
@app.post("/upload_file")
async def upload_file(request: Request, bucket_name: str = Form(...), file: UploadFile = File(...)):
    try:
        s3.upload_fileobj(file.file, bucket_name, file.filename)
        
        # List objects in the bucket after uploading the file
        response = s3.list_objects_v2(Bucket=bucket_name)
        contents = response.get("Contents", [])
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "buckets": s3.list_buckets().get("Buckets", []),
            "selected_bucket": bucket_name,
            "contents": contents
        })
    except ClientError as e:
        return {"error": f"Error uploading file: {str(e)}"}

# ---------------------- Delete File ----------------------
@app.post("/delete_file")
async def delete_file(request: Request, bucket_name: str = Form(...), key: str = Form(...)):
    try:
        s3.delete_object(Bucket=bucket_name, Key=key)
        
        # List objects in the bucket after deleting the file
        response = s3.list_objects_v2(Bucket=bucket_name)
        contents = response.get("Contents", [])
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "buckets": s3.list_buckets().get("Buckets", []),
            "selected_bucket": bucket_name,
            "contents": contents
        })
    except ClientError as e:
        return {"error": f"Error deleting file: {str(e)}"}

# ---------------------- Copy File ----------------------
@app.post("/copy_file")
async def copy_file(request: Request, src_bucket: str = Form(...), src_key: str = Form(...), dest_bucket: str = Form(...), dest_key: str = Form(...)):
    try:
        copy_source = {'Bucket': src_bucket, 'Key': src_key}
        s3.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)
        
        # List objects in the destination bucket after copying
        response = s3.list_objects_v2(Bucket=dest_bucket)
        contents = response.get("Contents", [])
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "buckets": s3.list_buckets().get("Buckets", []),
            "selected_bucket": dest_bucket,
            "contents": contents
        })
    except ClientError as e:
        return {"error": f"Error copying file: {str(e)}"}

# ---------------------- Move File ----------------------
@app.post("/move_file")
async def move_file(request: Request, src_bucket: str = Form(...), src_key: str = Form(...), dest_bucket: str = Form(...), dest_key: str = Form(...)):
    try:
        copy_source = {'Bucket': src_bucket, 'Key': src_key}
        s3.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)
        s3.delete_object(Bucket=src_bucket, Key=src_key)
        
        # List objects in the destination bucket after moving
        response = s3.list_objects_v2(Bucket=dest_bucket)
        contents = response.get("Contents", [])
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "buckets": s3.list_buckets().get("Buckets", []),
            "selected_bucket": dest_bucket,
            "contents": contents
        })
    except ClientError as e:
        return {"error": f"Error moving file: {str(e)}"}
