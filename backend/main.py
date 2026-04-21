# Built-in libraries
import base64
import json 
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import base64
import io
import urllib.request
from PIL import Image
from transformers import pipeline

import logging
import os

# External dependencies
from bson import ObjectId
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.db import get_database, upload_embeddings_to_mongo
from backend.logger import CustomFormatter
from backend.schema import FileContent, PostInfo
from backend.utils.common import (load_image_from_url_or_file,
                                  read_files_from_directory,
                                  serialize_object_id)
from backend.utils.embedding import find_top_matches, generate_text_embedding
from backend.utils.regex_ptr import extract_info
from backend.utils.steganography import (decode_text_from_image,
                                         encode_text_in_image)
from backend.utils.text_llm import (create_poem, decompose_user_text,
                                    expand_user_text_using_gemini,
                                    expand_user_text_using_gemma,
                                    text_to_image)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)

# Initialize FastAPI and CORS middleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Initialize the Deepfake Detection Model globally (Downloads once on startup)
# This model ("dima806/deepfake_vs_real_image_detection") classifies images as 'real' or 'fake'
print("Loading Deepfake Detection Model...")
deepfake_detector = pipeline("image-classification", model="dima806/deepfake_vs_real_image_detection")
print("Model loaded successfully!")

class EvidencePayload(BaseModel):
    image_url: str

# 2. Add the route to your FastAPI app
@app.post("/analyze-evidence")
async def analyze_evidence(payload: EvidencePayload):
    try:
        # Check if the image is a Base64 string (from your frontend upload) or a standard URL
        if payload.image_url.startswith("data:image"):
            header, encoded = payload.image_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        else:
            req = urllib.request.Request(payload.image_url, headers={'User-Agent': 'Mozilla/5.0'})
            image_data = urllib.request.urlopen(req).read()
            image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # 3. Run the Deepfake Detection
        results = deepfake_detector(image)
        
        # Results look like: [{'label': 'artificial', 'score': 0.99}, {'label': 'human', 'score': 0.01}]
        return {"analysis": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoints
@app.post("/text-generation")
async def get_post_and_expand_its_content(post_info: PostInfo):
    """Expand user input text for help message generation."""
    try:
        concatenated_text = (
            f"Name: {post_info.name}\n"
            f"Phone: {post_info.phone}\n"
            f"Location: {post_info.location}\n"
            f"Duration of Abuse: {post_info.duration_of_abuse}\n"
            f"Frequency of Incidents: {post_info.frequency_of_incidents}\n"
            f"Preferred Contact Method: {post_info.preferred_contact_method}\n"
            f"Current Situation: {post_info.current_situation}\n"
            f"Culprit Description: {post_info.culprit_description}\n"
            f"Custom Text: {post_info.custom_text}\n"
        )
        gemini_response = await expand_user_text_using_gemini(concatenated_text)
        gemma_response = await expand_user_text_using_gemma(concatenated_text)
        return {"gemini_response": gemini_response, "gemma_response": gemma_response}
    except Exception as e:
        logger.error("Error expanding text:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error expanding text: {e}")

@app.post("/img-generation")
async def create_image_from_prompt(input_data: str):
    """Generate an image based on a text prompt."""
    try:
        text_to_image(input_data)
        return {"received_text": input_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")


@app.post("/text-decomposition")
async def decompose_text_content(data: dict):
    """Decompose and extract information from user text."""
    try:
        text = data.get("text")
        decomposed_text = decompose_user_text(text)
        return {"extracted_data": extract_info(decomposed_text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decomposing text: {e}")


@app.post("/save-extracted-data")
async def save_extracted_data(data: dict):
    try:
        database = get_database()
        database["admin"].insert_one(data)
        return {"status": "Data saved successfully"}
    except Exception as e:
        logger.error("Error saving data:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error saving data: {e}")


@app.post("/encode")
async def encode_text_in_image_endpoint(
    text: str, img_url: str = None, file: UploadFile = File(None)
):
    """Encode text into an image."""
    try:
        image = load_image_from_url_or_file(img_url, file)
        encoded_image = encode_text_in_image(image, text)
        output_path = "encoded_image.png"
        encoded_image.save(output_path, format="PNG")
        return StreamingResponse(
            open(output_path, "rb"),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=encoded_image.png"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error encoding text in image: {e}"
        )


@app.post("/decode")
async def decode_text_from_image_endpoint(payload: EvidencePayload):
    """Decode text from an image."""
    try:
        if payload.image_url.startswith("data:image"):
            header, encoded = payload.image_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        else:
            req = urllib.request.Request(payload.image_url, headers={'User-Agent': 'Mozilla/5.0'})
            image_data = urllib.request.urlopen(req).read()
            image = Image.open(io.BytesIO(image_data)).convert("RGB")

        return {"decoded_text": decode_text_from_image(image)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error decoding text from image: {e}"
        )


@app.get("/poem-generation")
async def create_poem_endpoint(text: str):
    """Generate an inspirational poem based on input text."""
    try:
        return {"poem": create_poem(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating poem: {e}")


@app.post("/send-message")
async def send_message_to_twitter_endpoint(data: dict):
    """Send a message to Twitter."""
    try:
        import urllib.parse
        image_url = data.get("image_url", "")
        caption = data.get("caption", "")
        
        tweet_text = f"{caption}\n\nImage: {image_url}"
        encoded_text = urllib.parse.quote(tweet_text)
        x_url = f"https://x.com/compose/post?text={encoded_text}"
        return {"status": "success", "url": x_url}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error sending message to Twitter: {e}"
        )


@app.get("/get-admin-posts")
def get_all_posts():
    """Retrieve all posts from the database."""
    try:
        database = get_database()
        posts = [serialize_object_id(post) for post in database["admin"].find()]
        return JSONResponse(content=posts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving posts: {e}")


@app.get("/find-match")
def find_top_matching_posts(info: str, collection: str):
    """Find top matches based on embedding similarity."""
    try:
        database = get_database()
        description_vector = generate_text_embedding(info)
        top_matches = find_top_matches(database[collection], description_vector)
        return [serialize_object_id(match) for match in top_matches]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding matches: {e}")


@app.get("/get-post/{post_id}")
def get_post_by_id(post_id: str):
    """Retrieve a specific post by its ID."""
    try:
        database = get_database()
        post = database["admin"].find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return JSONResponse(content=serialize_object_id(post))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving post by ID: {e}")

@app.post("/close-issue/{issue_id}")
async def close_issue(issue_id: str):
    """Mark an issue as closed by updating its status."""
    try:
        database = get_database()
        result = database["admin"].update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {"status": "closed"}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Issue not found or already closed")
        return {"status": "Issue marked as closed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error closing issue: {e}")

@app.post("/upload_embeddings/")
async def upload_embeddings():
    """Upload embeddings to MongoDB."""
    try:
        file_contents = read_files_from_directory("backend/docs")
        upload_embeddings_to_mongo(file_contents)
        return {"message": "Embeddings uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading embeddings: {e}")


@app.post("/generate-image")
async def generate_image(data: dict):
    """Generate an image based on a text prompt using Pollinations AI and encode text inside it."""
    try:
        from io import BytesIO
        import urllib.parse
        
        prompt = data.get("prompt")
        text_to_encode = data.get("text_to_encode", prompt)
        print("Prompt: ", prompt)
        
        encoded_prompt = urllib.parse.quote(prompt)
        
        image_urls = []
        for i in range(3):
            seed = 42 + i
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&nologo=true"
            print("Processing Image URL: ", image_url)
            
            # 1. Download the generated image from Pollinations AI
            image = load_image_from_url_or_file(img_url=image_url, file=None)
            
            # 2. Encode the text/story inside the image pixels
            encoded_image = encode_text_in_image(image, text_to_encode)
            
            # 3. Convert to a Base64 data URL so the frontend can display it seamlessly
            buffered = BytesIO()
            encoded_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            image_urls.append(f"data:image/png;base64,{img_str}")
            
        return {"image_urls": image_urls}
    except Exception as e:
        logger.error("Error generating image: %s", e)
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")