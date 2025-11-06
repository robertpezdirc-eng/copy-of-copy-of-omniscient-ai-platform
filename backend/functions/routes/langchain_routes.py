
from fastapi import APIRouter
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

class LangChainRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate_text(request: LangChainRequest):
    """
    Receives a prompt and uses LangChain with Google Generative AI to generate text.
    """
    try:
        # It's good practice to ensure the API key is available
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        # Initialize the Chat Model
        llm = ChatGoogleGenerativeAI(model="gemini-pro")

        # Create a message to send to the model
        message = HumanMessage(content=request.prompt)

        # Invoke the model and get the response
        response = llm.invoke([message])

        return {"response": response.content}
    except Exception as e:
        # Log the exception for debugging
        print(f"Error in LangChain endpoint: {e}")
        # Return a more informative error to the client
        return {"error": str(e)}, 500
