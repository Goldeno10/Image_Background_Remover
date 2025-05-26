from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from rembg import remove, new_session
import numpy as np
from PIL import Image
from io import BytesIO
import uuid
import os
import redis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import torch
import logging
from pydantic import BaseModel, EmailStr
from typing import Optional
import json
import time

# Configuration
class Config:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    OUTPUT_DIR = "processed_images"
    GPU_ENABLED = torch.cuda.is_available()
    MODEL_MAP = {
        "u2net": new_session("u2net"),
        "u2netp": new_session("u2netp"),
        "u2net_human_seg": new_session("u2net_human_seg")
    }

# Initialize components
app = FastAPI()
redis_client = redis.from_url(Config.REDIS_URL)
logger = logging.getLogger(__name__)

os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

class ProcessingRequest(BaseModel):
    email: EmailStr
    model: str = "u2net"
    output_format: str = "png"
    quality: int = 95
    scale: float = 1.0

def send_notification_email(processing_id: str, email: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = Config.SMTP_USER
        msg["To"] = email
        msg["Subject"] = "Your Background Removal Processing is Complete"
        
        download_url = f"{Config.BASE_URL}/download/{processing_id}"
        body = f"""
        Your image processing is complete!\n
        Download URL: {download_url}\n
        This link will expire in 24 hours.
        """
        
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(msg)
            
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")

async def process_image_async(processing_id: str, request: ProcessingRequest, file: UploadFile):
    try:
        # Store initial state in Redis
        redis_client.setex(processing_id, 86400, json.dumps({
            "status": "processing",
            "email": request.email
        }))
        
        # Process image
        image_data = await file.read()
        img = Image.open(BytesIO(image_data))
        
        if request.scale != 1.0:
            img = img.resize((int(img.width * request.scale), 
                            int(img.height * request.scale)))
        
        session = Config.MODEL_MAP.get(request.model, Config.MODEL_MAP["u2net"])
        if Config.GPU_ENABLED:
            session = session.to("cuda")
        
        output = remove(np.array(img), session=session)
        result_img = Image.fromarray(output)
        
        # Save processed image
        filename = f"{processing_id}.{request.output_format}"
        output_path = os.path.join(Config.OUTPUT_DIR, filename)
        
        save_args = {}
        if request.output_format.lower() in ["jpeg", "jpg"]:
            save_args["quality"] = request.quality
            result_img = result_img.convert("RGB")
        
        result_img.save(output_path, **save_args)
        
        # Update Redis
        redis_client.setex(processing_id, 86400, json.dumps({
            "status": "completed",
            "email": request.email,
            "filename": filename
        }))
        
        # Send notification email
        send_notification_email(processing_id, request.email)
        
    except Exception as e:
        redis_client.setex(processing_id, 86400, json.dumps({
            "status": "failed",
            "error": str(e)
        }))
        logger.error(f"Processing failed: {str(e)}")

@app.post("/process")
async def create_processing_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    request: ProcessingRequest = None
):
    processing_id = str(uuid.uuid4())
    
    background_tasks.add_task(
        process_image_async,
        processing_id,
        request,
        file
    )
    
    return JSONResponse({
        "processing_id": processing_id,
        "status_url": f"{Config.BASE_URL}/status/{processing_id}",
        "message": "Processing started. You will receive an email when complete."
    })

@app.get("/status/{processing_id}")
def get_status(processing_id: str):
    result = redis_client.get(processing_id)
    if not result:
        raise HTTPException(404, "Processing ID not found")
    
    status_data = json.loads(result)
    return {"processing_id": processing_id, "status": status_data.get("status")}

@app.get("/download/{processing_id}")
def download_result(processing_id: str):
    result = redis_client.get(processing_id)
    if not result:
        raise HTTPException(404, "Processing ID not found or expired")
    
    status_data = json.loads(result)
    if status_data["status"] != "completed":
        raise HTTPException(425, "Processing not yet complete")
    
    filename = status_data.get("filename")
    file_path = os.path.join(Config.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    
    return FileResponse(
        file_path,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# Optimization Implementations
if Config.GPU_ENABLED:
    logger.info("GPU acceleration enabled")
    for model in Config.MODEL_MAP.values():
        model.to("cuda")

# Scheduled cleanup task
from apscheduler.schedulers.background import BackgroundScheduler

def cleanup_expired_files():
    try:
        # Clean Redis entries
        for key in redis_client.scan_iter("*"):
            if redis_client.ttl(key) < 0:
                redis_client.delete(key)
        
        # Clean file system
        for filename in os.listdir(Config.OUTPUT_DIR):
            file_path = os.path.join(Config.OUTPUT_DIR, filename)
            if os.path.getmtime(file_path) < (time.time() - 86400):
                os.remove(file_path)
                
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_expired_files, 'interval', hours=1)
scheduler.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)