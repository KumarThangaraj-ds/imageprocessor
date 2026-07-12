from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai import errors
#from openai import OpenAI
import base64

# Configure the client to automatically retry on common transient failures
retry_options = types.HttpRetryOptions(
    attempts=5,
    initial_delay=2.0,
    max_delay=60.0,
    http_status_codes=[408, 429, 500, 502, 503, 504]
)

#client = OpenAI()
client = genai.Client(http_options=types.HttpOptions(retry_options=retry_options))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    image_base64: str
    question: str

def GetGPTResponse (image_data, question):
	print ("before GPT Call")
	response = client.responses.create(
		model="gpt-5",
		input="Explain Python decorators in simple terms."
	)

	print (response.output_text)

	return response.output_text

def GetGeminiResponse (image_data, question):
    image_part = types.Part.from_bytes(data=image_data,mime_type='image/png')
    print ("before Gemini Call")
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[
                image_part, 
                question + "give me only the value in the response and in case of number or amount remove the mantissa separator and decimal separator should not be missed. query can ask the category for highest amount, in that case category name to be shared not amount. similarly highest percentage of the category can be asked, dont give percentage, give name of the item",
            ]
        )
        return response.text
    except errors.ClientError as e:
        if e.code == 429:
            return ("Rate limit reached. Back off and retry.")
        if e.code == 400:
            return (f"Invalid Argument code:{e.code}, message:{e.message}")
        if e.code == 403:
            return ("Forbidden request")
        if e.code == 404:
            return ("Not Found")
    except errors.ServerError as e:
        return (f"Server Error [{e.code}]: {e.message}")

    except errors.APIError as e:
        return (f"API Error: {e}")

    except Exception as e:
        return (f"Unexpected non-API error: {e}")

def GetEncodedLocalFile ():
	file_path = "images1.png"
	encoded_bytes = ''
	with open(file_path, "rb") as image_file:
		# Read the file and encode it to base64 bytes
		encoded_bytes = base64.b64encode(image_file.read()) 
	return encoded_bytes
	
@app.post("/answer-image")
async def answer_image(req: ImageRequest):
    image_data = req.image_base64
    print (req.question)
    print (image_data)
    if image_data.startswith("data:"):
        image_data = image_data.split(",", 1)[1]
    encoded = image_data.encode("utf-8")
    decoded = base64.b64decode(encoded)
    question = req.question
    #image_data = GetEncodedLocalFile ()
    # send image_data + question to your multimodal model here
    answer = "4089.35"
    #gptres = GetGPTResponse (image_data, question)
    answer = GetGeminiResponse (decoded, question)
    print (f"answer: {answer}")
    return {"answer": str(answer)}
