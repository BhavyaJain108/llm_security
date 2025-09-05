from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from conversation_graph import ConversationManager
from models_config import get_model_providers, get_models_for_provider, AVAILABLE_MODELS
from knowledge_system import KnowledgeManager, KnowledgeType, AccessPattern, KnowledgeSource
from knowledge_upload import KnowledgeUploader, upload_90_message_example, upload_manipulation_architecture
from trainable_agent import PersonalityDatabase, PersonalityAgent
from simple_chat import SimpleChatSession
import uvicorn
import os
import traceback
import json
from anthropic import AuthenticationError, APIError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Retro Chat Assistant")

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize conversation manager
conversation_manager = ConversationManager()

# Initialize knowledge management system
knowledge_manager = KnowledgeManager()
knowledge_uploader = KnowledgeUploader()

# Initialize training system
# Initialize personality database
personality_db = PersonalityDatabase()
current_training_sessions = {}  # Store active training sessions

# Store active simple chat sessions
active_chat_sessions = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main chat interface"""
    conversations = conversation_manager.list_conversations()
    model_providers = get_model_providers()
    models_by_provider = {provider_id: get_models_for_provider(provider_id) for provider_id, _ in model_providers}
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "conversations": conversations,
        "user_agent_messages": [],
        "agent_llm_messages": [],
        "model_providers": model_providers,
        "models_by_provider": models_by_provider
    })

@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...), conversation_id: str = Form(None)):
    """Handle chat messages"""
    try:
        result = conversation_manager.chat(message, conversation_id)
        conversations = conversation_manager.list_conversations()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "conversations": conversations,
            "current_conversation_id": result["conversation_id"],
            "messages": result["messages"],
            "last_response": result["ai_response"]
        })
    
    except AuthenticationError as e:
        conversations = conversation_manager.list_conversations()
        error_message = "❌ Authentication Error: Invalid Claude API key. Please check your .env file and ensure you have a valid API key from https://console.anthropic.com/"
        
        # Create error response
        messages = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_message}
        ]
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "conversations": conversations,
            "current_conversation_id": conversation_id,
            "messages": messages,
            "error": error_message
        })
    
    except APIError as e:
        conversations = conversation_manager.list_conversations()
        error_message = f"❌ API Error: {str(e)}"
        
        messages = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_message}
        ]
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "conversations": conversations,
            "current_conversation_id": conversation_id,
            "messages": messages,
            "error": error_message
        })
    
    except Exception as e:
        conversations = conversation_manager.list_conversations()
        error_message = f"❌ Unexpected Error: {str(e)}"
        
        messages = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_message}
        ]
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "conversations": conversations,
            "current_conversation_id": conversation_id,
            "messages": messages,
            "error": error_message
        })

@app.get("/conversation/{conversation_id}", response_class=HTMLResponse)
async def load_conversation(request: Request, conversation_id: str):
    """Load a specific conversation"""
    user_agent_messages, agent_llm_messages = conversation_manager.load_dual_conversation(conversation_id)
    conversations = conversation_manager.list_conversations()
    model_providers = get_model_providers()
    models_by_provider = {provider_id: get_models_for_provider(provider_id) for provider_id, _ in model_providers}
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "conversations": conversations,
        "current_conversation_id": conversation_id,
        "user_agent_messages": user_agent_messages,
        "agent_llm_messages": agent_llm_messages,
        "model_providers": model_providers,
        "models_by_provider": models_by_provider
    })

@app.post("/new-test", response_class=HTMLResponse)
async def new_test(request: Request, model_provider: str = Form(...), target_model: str = Form(...), 
                  test_prompt: str = Form(...), max_conversation_length: int = Form(...), 
                  max_retries: int = Form(...), personality_id: str = Form(None)):
    """Start a new security test with specified parameters"""
    conversations = conversation_manager.list_conversations()
    model_providers = get_model_providers()
    models_by_provider = {provider_id: get_models_for_provider(provider_id) for provider_id, _ in model_providers}
    
    # Create new test session
    test_params = {
        "model_provider": model_provider,
        "target_model": target_model,
        "test_prompt": test_prompt,
        "max_conversation_length": max_conversation_length,
        "max_retries": max_retries,
        "personality_id": personality_id
    }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "conversations": conversations,
        "current_conversation_id": None,
        "user_agent_messages": [],
        "agent_llm_messages": [],
        "model_providers": model_providers,
        "models_by_provider": models_by_provider,
        "test_params": test_params
    })

@app.post("/delete-conversation/{conversation_id}", response_class=HTMLResponse)
async def delete_conversation(request: Request, conversation_id: str):
    """Delete a conversation"""
    conversation_manager.delete_conversation(conversation_id)
    conversations = conversation_manager.list_conversations()
    model_providers = get_model_providers()
    models_by_provider = {provider_id: get_models_for_provider(provider_id) for provider_id, _ in model_providers}
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "conversations": conversations,
        "current_conversation_id": None,
        "user_agent_messages": [],
        "agent_llm_messages": [],
        "model_providers": model_providers,
        "models_by_provider": models_by_provider
    })

@app.get("/static/style.css")
async def get_css():
    """Serve CSS with no-cache headers"""
    return FileResponse(
        "static/style.css", 
        media_type="text/css",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    return FileResponse("static/favicon.ico", media_type="image/x-icon")

@app.get("/knowledge-management", response_class=HTMLResponse)
async def knowledge_management(request: Request):
    """Knowledge base management interface"""
    conversations = conversation_manager.list_conversations()
    
    # Get all knowledge sources for display
    all_knowledge = knowledge_manager.get_all_knowledge_sources()
    
    return templates.TemplateResponse("knowledge_management.html", {
        "request": request,
        "conversations": conversations,
        "knowledge_sources": all_knowledge
    })

@app.post("/upload-success-example")
async def upload_success_example(
    title: str = Form(...),
    conversation_text: str = Form(...),
    description: str = Form(...),
    target_models: str = Form(""),
    attack_objectives: str = Form("")
):
    """Upload a successful attack conversation example"""
    try:
        target_models_list = [m.strip() for m in target_models.split(",") if m.strip()]
        attack_objectives_list = [o.strip() for o in attack_objectives.split(",") if o.strip()]
        
        knowledge_id = knowledge_uploader.upload_success_example(
            title=title,
            conversation_text=conversation_text,
            description=description,
            target_models=target_models_list,
            attack_objectives=attack_objectives_list
        )
        
        return JSONResponse({
            "success": True,
            "knowledge_id": knowledge_id,
            "message": "Success example uploaded successfully"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)

@app.post("/upload-manipulation-framework")
async def upload_manipulation_framework(
    title: str = Form(...),
    framework_text: str = Form(...),
    description: str = Form(...),
    psychological_principles: str = Form("")
):
    """Upload a psychological manipulation framework"""
    try:
        principles_list = [p.strip() for p in psychological_principles.split(",") if p.strip()]
        
        knowledge_id = knowledge_uploader.upload_manipulation_framework(
            title=title,
            framework_text=framework_text,
            description=description,
            psychological_principles=principles_list
        )
        
        return JSONResponse({
            "success": True,
            "knowledge_id": knowledge_id,
            "message": "Manipulation framework uploaded successfully"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)

@app.post("/upload-prompt-technique")
async def upload_prompt_technique(
    title: str = Form(...),
    technique_description: str = Form(...),
    example_prompts: str = Form(...),
    target_models: str = Form(""),
    effectiveness_notes: str = Form("")
):
    """Upload a specific prompt engineering technique"""
    try:
        target_models_list = [m.strip() for m in target_models.split(",") if m.strip()]
        
        knowledge_id = knowledge_uploader.upload_prompt_technique(
            title=title,
            technique_description=technique_description,
            example_prompts=example_prompts,
            target_models=target_models_list,
            effectiveness_notes=effectiveness_notes
        )
        
        return JSONResponse({
            "success": True,
            "knowledge_id": knowledge_id,
            "message": "Prompt technique uploaded successfully"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)

@app.get("/api/knowledge-sources")
async def list_knowledge_sources():
    """API endpoint to list all knowledge sources"""
    try:
        knowledge_sources = knowledge_manager.get_all_knowledge_sources()
        return JSONResponse({
            "success": True,
            "knowledge_sources": [
                {
                    "id": k.id,
                    "title": k.title,
                    "description": k.description,
                    "knowledge_type": k.knowledge_type.value,
                    "access_pattern": k.access_pattern.value,
                    "effectiveness_score": k.effectiveness_score,
                    "success_count": k.success_count,
                    "attempt_count": k.attempt_count,
                    "created_date": k.created_date.isoformat(),
                    "tags": k.tags
                } for k in knowledge_sources
            ]
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.delete("/api/knowledge-sources/{knowledge_id}")
async def delete_knowledge_source(knowledge_id: str):
    """Delete a knowledge source"""
    try:
        success = knowledge_manager.delete_knowledge_source(knowledge_id)
        if success:
            return JSONResponse({
                "success": True,
                "message": "Knowledge source deleted successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Knowledge source not found"
            }, status_code=404)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/chat-stream")
async def chat_stream(message: str = Form(...), conversation_id: str = Form(None)):
    """Stream chat responses"""
    def generate_stream():
        try:
            for chunk in conversation_manager.chat_stream(message, conversation_id):
                data_line = f"data: {json.dumps(chunk)}\n\n"
                yield data_line
        except AuthenticationError as e:
            error_chunk = {
                "type": "error",
                "error": "Authentication Error: Invalid Claude API key. Please check your .env file."
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        except APIError as e:
            error_chunk = {
                "type": "error", 
                "error": f"API Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        except Exception as e:
            error_chunk = {
                "type": "error",
                "error": f"Unexpected Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.get("/dual-chat-stream")
async def dual_chat_stream_get(message: str, conversation_id: str = None, test_params: str = None):
    """Stream dual conversation responses via GET for EventSource"""
    def generate_stream():
        try:
            # Parse test parameters if provided
            parsed_test_params = None
            if test_params:
                try:
                    parsed_test_params = json.loads(test_params)
                except json.JSONDecodeError:
                    pass
            
            for chunk in conversation_manager.dual_chat_stream(message, conversation_id, parsed_test_params):
                data_line = f"data: {json.dumps(chunk)}\n\n"
                yield data_line
        except AuthenticationError as e:
            error_chunk = {
                "type": "error",
                "error": "Authentication Error: Invalid Claude API key. Please check your .env file."
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        except APIError as e:
            error_chunk = {
                "type": "error", 
                "error": f"API Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        except Exception as e:
            error_chunk = {
                "type": "error",
                "error": f"Unexpected Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Simple Chat routes
@app.get("/simple-chat", response_class=HTMLResponse)
async def simple_chat_page(request: Request):
    """Render the simple chat interface"""
    return templates.TemplateResponse("simple_chat.html", {
        "request": request
    })

@app.post("/api/simple-chat/start")
async def start_chat_session():
    """Start a new simple chat session"""
    try:
        session = SimpleChatSession()
        session_id = session.session_id
        active_chat_sessions[session_id] = session
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "message": "Chat session started"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/simple-chat/{session_id}/message")
async def send_chat_message(session_id: str, request: Request):
    """Send a message in a chat session"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        
        if not message:
            return JSONResponse({
                "success": False,
                "error": "Message is required"
            }, status_code=400)
        
        if session_id not in active_chat_sessions:
            return JSONResponse({
                "success": False,
                "error": "Chat session not found"
            }, status_code=404)
        
        session = active_chat_sessions[session_id]
        response = session.chat(message)
        
        return JSONResponse({
            "success": True,
            "response": response,
            "conversation": session.conversation
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/simple-chat/{session_id}/edit")
async def edit_chat_message(session_id: str, request: Request):
    """Edit a message in a chat session"""
    try:
        data = await request.json()
        message_index = data.get("message_index")
        new_content = data.get("new_content", "").strip()
        
        if message_index is None:
            return JSONResponse({
                "success": False,
                "error": "Message index is required"
            }, status_code=400)
        
        if not new_content:
            return JSONResponse({
                "success": False,
                "error": "New content is required"
            }, status_code=400)
        
        if session_id not in active_chat_sessions:
            return JSONResponse({
                "success": False,
                "error": "Chat session not found"
            }, status_code=404)
        
        session = active_chat_sessions[session_id]
        response = session.edit_message(message_index, new_content)
        
        return JSONResponse({
            "success": True,
            "response": response,
            "conversation": session.conversation
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/simple-chat/{session_id}/save")
async def save_chat_as_personality(session_id: str, request: Request):
    """Save chat session as personality"""
    try:
        data = await request.json()
        personality_name = data.get("personality_name", "").strip()
        
        if not personality_name:
            return JSONResponse({
                "success": False,
                "error": "Personality name is required"
            }, status_code=400)
        
        if session_id not in active_chat_sessions:
            return JSONResponse({
                "success": False,
                "error": "Chat session not found"
            }, status_code=404)
        
        session = active_chat_sessions[session_id]
        
        if len(session.conversation) == 0:
            return JSONResponse({
                "success": False,
                "error": "No conversation to save"
            }, status_code=400)
        
        result = session.save_as_personality(personality_name)
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/simple-chat/{session_id}/conversation")
async def get_conversation(session_id: str):
    """Get current conversation for a chat session"""
    try:
        if session_id not in active_chat_sessions:
            return JSONResponse({
                "success": False,
                "error": "Chat session not found"
            }, status_code=404)
        
        session = active_chat_sessions[session_id]
        
        return JSONResponse({
            "success": True,
            "conversation": session.conversation,
            "preview": session.get_conversation_preview()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/simple-chat/saved-personalities")
async def list_saved_personalities():
    """List all saved personalities"""
    try:
        # Use the simple chat session method to list personalities
        temp_session = SimpleChatSession()
        personalities = temp_session.list_saved_personalities()
        
        return JSONResponse({
            "success": True,
            "personalities": personalities
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Training routes
@app.get("/train", response_class=HTMLResponse)
async def training_page(request: Request):
    """Render the training chat interface"""
    return templates.TemplateResponse("train_agent.html", {
        "request": request
    })

@app.post("/simple-chat")
async def simple_chat_endpoint(request: Request):
    """Simple chat endpoint that maintains conversation history"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        model = data.get("model", "claude-3-5-sonnet-20241022")
        conversation_history = data.get("conversation_history", [])
        
        # Debug logging
        print(f"DEBUG: Received model: '{model}'")
        print(f"DEBUG: Received message: '{message}'")
        print(f"DEBUG: Conversation history length: {len(conversation_history)}")
        
        if not message:
            return JSONResponse({
                "success": False,
                "error": "Message is required"
            })
        
        # Simple direct call to Claude
        from anthropic import Anthropic
        
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            return JSONResponse({
                "success": False,
                "error": "Claude API key not found. Please check your .env file."
            })
        
        client = Anthropic(api_key=api_key)
        
        # Build messages array from conversation history
        messages = []
        
        # Add conversation history (excluding timestamps and metadata)
        for msg in conversation_history:
            if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"] and msg.get("content"):
                messages.append({
                    "role": msg["role"],
                    "content": str(msg["content"]).strip()
                })
        
        # Add current message only if it's not already in the conversation history
        # Check if the last message in history is the current message
        current_message_already_included = False
        if (messages and 
            messages[-1]["role"] == "user" and 
            messages[-1]["content"].strip() == message.strip()):
            current_message_already_included = True
            print(f"DEBUG: Current message already in conversation history")
        
        if not current_message_already_included:
            messages.append({"role": "user", "content": message})
            print(f"DEBUG: Added current message to API call")
        
        # Validate we have at least one message
        if len(messages) == 0:
            return JSONResponse({
                "success": False,
                "error": "No valid messages to send"
            })
        
        print(f"DEBUG: Sending {len(messages)} messages to API")
        print(f"DEBUG: About to call API with model: '{model}'")
        
        # Call the API with full conversation context
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            messages=messages
        )
        
        # Debug the actual response object
        print(f"DEBUG: API Response Details:")
        print(f"DEBUG: Response type: {type(response)}")
        print(f"DEBUG: Response attributes: {dir(response)}")
        print(f"DEBUG: Response model field: {getattr(response, 'model', 'NO MODEL FIELD')}")
        print(f"DEBUG: Response usage: {getattr(response, 'usage', 'NO USAGE FIELD')}")
        
        # Safely check response content
        if not hasattr(response, 'content') or not response.content:
            print(f"DEBUG: No content in response")
            return JSONResponse({
                "success": False,
                "error": f"No content returned from model {model}"
            })
        
        if len(response.content) == 0:
            print(f"DEBUG: Empty content array")
            return JSONResponse({
                "success": False,
                "error": f"Empty content returned from model {model}"
            })
        
        # Get the response text safely
        response_text = ""
        if hasattr(response.content[0], 'text'):
            response_text = response.content[0].text
        elif hasattr(response.content[0], 'content'):
            response_text = str(response.content[0].content)
        else:
            response_text = str(response.content[0])
        
        print(f"DEBUG: Response content preview: {response_text[:100]}...")
        
        # Check if response has any metadata about which model actually processed it
        if hasattr(response, 'model'):
            print(f"DEBUG: Actual processing model: {response.model}")
        if hasattr(response, 'usage') and hasattr(response.usage, 'model'):
            print(f"DEBUG: Usage model: {response.usage.model}")
        
        return JSONResponse({
            "success": True,
            "response": response_text
        })
        
    except Exception as e:
        print(f"DEBUG: Error with model {model}: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Error with model {model}: {str(e)}"
        })

@app.get("/personality_creator", response_class=HTMLResponse)
async def personality_creator_page(request: Request):
    """Render the personality creation interface"""
    return templates.TemplateResponse("personality_creator.html", {
        "request": request
    })

@app.post("/create_personality")
async def create_personality(request: Request):
    """Create a new personality from conversation content"""
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        conversation_content = data.get("conversation_content", "")
        provider = data.get("provider", "anthropic")
        model = data.get("model", None)
        parser_type = data.get("parser_type", None)
        
        print(f"DEBUG: Creating personality - Name: {name}, Content length: {len(conversation_content)}")
        
        # Validate inputs
        if not name:
            return JSONResponse({
                "success": False,
                "error": "Personality name is required"
            })
        
        if len(name) > 200:
            return JSONResponse({
                "success": False,
                "error": "Personality name must be 200 characters or less"
            })
        
        if not conversation_content.strip():
            return JSONResponse({
                "success": False,
                "error": "Conversation content is required"
            })
        
        # Create personality
        personality_id = personality_db.create_personality(
            name=name,
            conversation_content=conversation_content,
            provider=provider,
            model=model,
            parser_type=parser_type
        )
        
        print(f"DEBUG: Personality created with ID: {personality_id}")
        
        # Get info about the created personality
        agent = personality_db.get_personality(personality_id)
        info = agent.get_info() if agent else {}
        
        print(f"DEBUG: Personality agent retrieved: {agent is not None}")
        print(f"DEBUG: Personality info: {info}")
        
        return JSONResponse({
            "success": True,
            "personality_id": personality_id,
            "api_endpoint": f"/api/personality/{personality_id}/generate",
            "info": info,
            "message": f"Personality '{name}' created successfully"
        })
    
    except Exception as e:
        print(f"DEBUG: Error creating personality: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/upload_personality")
async def upload_personality(
    file: UploadFile = File(...),
    name: str = Form(...),
    provider: str = Form("anthropic"),
    model: str = Form(None),
    parser_type: str = Form(None)
):
    """Upload a conversation file to create personality"""
    try:
        # Validate name
        if not name.strip():
            return JSONResponse({
                "success": False,
                "error": "Personality name is required"
            })
        
        if len(name) > 200:
            return JSONResponse({
                "success": False,
                "error": "Personality name must be 200 characters or less"
            })
        
        # Handle file differently based on parser type
        if parser_type == 'anthropic':
            # For Anthropic parser, save the .docx file and pass file path
            import tempfile
            import os
            
            # Create temp file with .docx extension
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                temp_file_path = tmp_file.name
            
            try:
                # Create personality using file path
                personality_id = personality_db.create_personality(
                    name=name,
                    conversation_content=temp_file_path,
                    provider=provider,
                    model=model,
                    parser_type=parser_type,
                    is_file_path=True
                )
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        else:
            # For other parsers, read file content as text
            content = await file.read()
            conversation_content = content.decode('utf-8')
            
            personality_id = personality_db.create_personality(
                name=name,
                conversation_content=conversation_content,
                provider=provider,
                model=model,
                parser_type=parser_type
            )
        
        # Get info about the created personality
        agent = personality_db.get_personality(personality_id)
        info = agent.get_info() if agent else {}
        
        return JSONResponse({
            "success": True,
            "personality_id": personality_id,
            "api_endpoint": f"/api/personality/{personality_id}/generate",
            "info": info,
            "message": f"Personality '{name}' created successfully from uploaded file"
        })
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/analyze_conversation")
async def analyze_conversation(request: Request):
    """Analyze conversation content before creating personality"""
    try:
        data = await request.json()
        conversation_content = data.get("conversation_content", "")
        parser_type = data.get("parser_type", None)
        
        if not conversation_content.strip():
            return JSONResponse({
                "success": False,
                "error": "Conversation content is required"
            })
        
        analysis = personality_db.analyze_conversation(conversation_content, parser_type)
        
        return JSONResponse({
            "success": True,
            "analysis": analysis
        })
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/personalities")
async def list_personalities():
    """List all created personalities"""
    try:
        personalities = personality_db.list_personalities()
        return JSONResponse({
            "success": True,
            "personalities": personalities
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/available_parsers")
async def get_available_parsers():
    """Get list of available conversation parsers"""
    try:
        from conversation_parsers import ConversationParserFactory
        parser_factory = ConversationParserFactory()
        parsers = parser_factory.get_available_parsers()
        return JSONResponse({
            "success": True,
            "parsers": parsers
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/api/personality/{personality_id}/generate")
async def generate_with_personality(personality_id: str, request: Request):
    """Generate response using a specific personality"""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        
        if not prompt.strip():
            return JSONResponse({
                "success": False,
                "error": "Prompt is required"
            })
        
        agent = personality_db.get_personality(personality_id)
        if not agent:
            return JSONResponse({
                "success": False,
                "error": f"Personality {personality_id} not found"
            })
        
        response = agent.generate_response(prompt)
        
        return JSONResponse({
            "success": True,
            "response": response,
            "personality_id": personality_id
        })
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.delete("/personality/{personality_id}")
async def delete_personality(personality_id: str):
    """Delete a personality"""
    try:
        success = personality_db.delete_personality(personality_id)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Personality {personality_id} deleted successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": f"Personality {personality_id} not found"
            })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/train_chat_stream")
async def train_chat_stream(request: Request):
    """Stream training chat responses - DEPRECATED"""
    raise HTTPException(status_code=501, detail="Old training system deprecated. Use /create_personality instead")

@app.post("/mark_successful_break")
async def mark_successful_break(request: Request):
    """Mark the last exchange as a successful break"""
    try:
        data = await request.json()
        session_id = data.get("session_id", "default")
        technique_used = data.get("technique_used", "")
        
        if session_id in current_training_sessions:
            training_agent = current_training_sessions[session_id]
            
            # Get the last user-agent exchange
            history = training_agent.conversation_history
            if len(history) >= 2:
                user_msg = history[-2]["content"] if history[-2]["role"] == "user" else ""
                agent_msg = history[-1]["content"] if history[-1]["role"] == "assistant" else ""
                
                if user_msg and agent_msg:
                    training_agent.add_successful_break(user_msg, agent_msg, technique_used)
                    
                    return JSONResponse({
                        "success": True,
                        "message": "Break recorded successfully",
                        "training_summary": training_agent.get_training_summary()
                    })
            
            return JSONResponse({
                "success": False,
                "error": "No valid exchange found to mark as break"
            })
        
        return JSONResponse({
            "success": False,
            "error": "Training session not found"
        })
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/save_trained_agent")
async def save_trained_agent(request: Request):
    """Save a trained agent"""
    try:
        data = await request.json()
        name = data.get("name", "")
        description = data.get("description", "")
        session_id = data.get("session_id", "default")
        
        if not name.strip():
            return JSONResponse({
                "success": False,
                "error": "Agent name is required"
            })
        
        if session_id in current_training_sessions:
            training_agent = current_training_sessions[session_id]
            agent_data = training_agent.export_trained_agent(name, description)
            agent_id = trained_agent_db.save_agent(agent_data)
            
            return JSONResponse({
                "success": True,
                "agent_id": agent_id,
                "message": f"Agent '{name}' saved successfully"
            })
        
        return JSONResponse({
            "success": False,
            "error": "Training session not found"
        })
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/trained_agents")
async def list_trained_agents():
    """List all trained agents"""
    try:
        agents = trained_agent_db.list_agents()
        return JSONResponse({
            "success": True,
            "agents": agents
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/training_summary/{session_id}")
async def get_training_summary(session_id: str):
    """Get training summary for a session"""
    try:
        if session_id in current_training_sessions:
            training_agent = current_training_sessions[session_id]
            summary = training_agent.get_training_summary()
            return JSONResponse({
                "success": True,
                "summary": summary
            })
        
        return JSONResponse({
            "success": False,
            "error": "Training session not found"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/reset_training/{session_id}")
async def reset_training(session_id: str):
    """Reset training for a session"""
    try:
        if session_id in current_training_sessions:
            training_agent = current_training_sessions[session_id]
            training_agent.reset_training()
            return JSONResponse({
                "success": True,
                "message": "Training reset successfully"
            })
        
        return JSONResponse({
            "success": False,
            "error": "Training session not found"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)