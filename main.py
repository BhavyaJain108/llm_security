from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from conversation_graph import ConversationManager
from models_config import get_model_providers, get_models_for_provider, AVAILABLE_MODELS
from knowledge_system import KnowledgeManager, KnowledgeType, AccessPattern, KnowledgeSource
from knowledge_upload import KnowledgeUploader, upload_90_message_example, upload_manipulation_architecture
from trainable_agent import TrainableAttackAgent, TrainedAgentDatabase
import uvicorn
import os
import traceback
import json
from anthropic import AuthenticationError, APIError

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
trained_agent_db = TrainedAgentDatabase()
current_training_sessions = {}  # Store active training sessions

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
                  test_prompt: str = Form(...), max_conversation_length: int = Form(...), max_retries: int = Form(...)):
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
        "max_retries": max_retries
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

# Training routes
@app.get("/train", response_class=HTMLResponse)
async def training_page(request: Request):
    """Render the agent training interface"""
    return templates.TemplateResponse("train_agent.html", {
        "request": request
    })

@app.post("/train_chat_stream")
async def train_chat_stream(request: Request):
    """Stream training chat responses"""
    try:
        data = await request.json()
        message = data.get("message", "")
        conversation_history = data.get("conversation_history", [])
        session_id = data.get("session_id", "default")
        agent_type = data.get("agent_type", "base")
        model_name = data.get("model_name", "claude-3-5-sonnet-20241022")
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create training session
        if session_id not in current_training_sessions:
            current_training_sessions[session_id] = TrainableAttackAgent(agent_type, model_name)
        
        training_agent = current_training_sessions[session_id]
        
        def generate_stream():
            try:
                for chunk in training_agent.chat_stream(message):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                error_chunk = {
                    "type": "error",
                    "error": f"Training Error: {str(e)}"
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
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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