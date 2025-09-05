"""
Configuration for available AI models for testing
"""

AVAILABLE_MODELS = {
    "anthropic": {
        "name": "Anthropic",
        "models": {
            "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (Latest)",
            "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet (June 2024)",
            "claude-3-sonnet-20240229": "Claude 3 Sonnet",
            "claude-3-haiku-20240307": "Claude 3 Haiku",
            "claude-3-opus-20240229": "Claude 3 Opus",
            "claude-opus-4-1-20250805": "Claude Opus 4.1"
        }
    }
}

def get_model_providers():
    """Get list of available model providers"""
    return [(key, value["name"]) for key, value in AVAILABLE_MODELS.items()]

def get_models_for_provider(provider):
    """Get list of models for a specific provider"""
    if provider in AVAILABLE_MODELS:
        return [(key, value) for key, value in AVAILABLE_MODELS[provider]["models"].items()]
    return []

def get_model_display_name(provider, model_id):
    """Get display name for a specific model"""
    if provider in AVAILABLE_MODELS and model_id in AVAILABLE_MODELS[provider]["models"]:
        return AVAILABLE_MODELS[provider]["models"][model_id]
    return model_id