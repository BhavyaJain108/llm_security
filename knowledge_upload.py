"""
Knowledge Upload and Management Interface
"""

from datetime import datetime
from typing import List
from knowledge_system import KnowledgeManager, KnowledgeSource, KnowledgeType, AccessPattern
import uuid

class KnowledgeUploader:
    """Helper class for uploading and managing knowledge sources"""
    
    def __init__(self):
        self.knowledge_manager = KnowledgeManager()
    
    def upload_success_example(self, 
                             title: str,
                             conversation_text: str,
                             description: str,
                             target_models: List[str] = None,
                             attack_objectives: List[str] = None) -> str:
        """
        Upload a successful attack conversation example
        
        Args:
            title: Brief title for the example
            conversation_text: The full conversation text
            description: What made this attack successful
            target_models: Which models this example applies to
            attack_objectives: What types of attacks this demonstrates
        """
        
        if target_models is None:
            target_models = []
        if attack_objectives is None:
            attack_objectives = []
            
        knowledge = KnowledgeSource(
            id=str(uuid.uuid4()),
            title=title,
            content=conversation_text,
            description=description,
            knowledge_type=KnowledgeType.SUCCESS_EXAMPLES,
            access_pattern=AccessPattern.EXECUTION_PHASE,
            relevant_models=target_models,
            attack_objectives=attack_objectives,
            difficulty_level=3,  # Default to medium difficulty
            source="manual_upload",
            created_date=datetime.now(),
            tags=["conversation", "successful_attack"]
        )
        
        if self.knowledge_manager.add_knowledge_source(knowledge):
            return knowledge.id
        else:
            raise Exception("Failed to upload knowledge source")
    
    def upload_manipulation_framework(self,
                                    title: str, 
                                    framework_text: str,
                                    description: str,
                                    psychological_principles: List[str] = None) -> str:
        """
        Upload a strategic manipulation framework
        
        Args:
            title: Name of the framework
            framework_text: The detailed framework content
            description: How this framework applies to AI jailbreaking
            psychological_principles: Key principles this framework leverages
        """
        
        tags = ["framework", "psychology", "strategy"]
        if psychological_principles:
            tags.extend(psychological_principles)
            
        knowledge = KnowledgeSource(
            id=str(uuid.uuid4()),
            title=title,
            content=framework_text,
            description=description,
            knowledge_type=KnowledgeType.MANIPULATION_FRAMEWORK,
            access_pattern=AccessPattern.PLANNING_PHASE,
            relevant_models=[],  # Applies to all models
            attack_objectives=[],  # Applies to all attack types
            difficulty_level=4,  # Frameworks are typically advanced
            source="manual_upload", 
            created_date=datetime.now(),
            tags=tags
        )
        
        if self.knowledge_manager.add_knowledge_source(knowledge):
            return knowledge.id
        else:
            raise Exception("Failed to upload framework")
    
    def upload_prompt_technique(self,
                               title: str,
                               technique_description: str,
                               example_prompts: str,
                               target_models: List[str] = None,
                               effectiveness_notes: str = "") -> str:
        """
        Upload a specific prompt engineering technique
        """
        
        if target_models is None:
            target_models = []
            
        content = f"TECHNIQUE: {technique_description}\n\nEXAMPLES:\n{example_prompts}\n\nNOTES: {effectiveness_notes}"
        
        knowledge = KnowledgeSource(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            description=technique_description,
            knowledge_type=KnowledgeType.PROMPT_TECHNIQUES,
            access_pattern=AccessPattern.EXECUTION_PHASE,
            relevant_models=target_models,
            attack_objectives=[],
            difficulty_level=2,  # Techniques are typically basic-medium
            source="manual_upload",
            created_date=datetime.now(), 
            tags=["prompt_engineering", "technique"]
        )
        
        if self.knowledge_manager.add_knowledge_source(knowledge):
            return knowledge.id
        else:
            raise Exception("Failed to upload technique")

# Example usage functions for the two knowledge sources you mentioned

def upload_90_message_example(uploader: KnowledgeUploader, conversation_text: str) -> str:
    """Upload the 90-message successful jailbreak example"""
    
    return uploader.upload_success_example(
        title="90-Message Successful Jailbreak",
        conversation_text=conversation_text,
        description="""
        Extended conversation demonstrating gradual manipulation techniques.
        Shows how to build rapport, establish context, and incrementally push boundaries.
        Key strategies: persistence, rapport building, incremental boundary testing, 
        context switching, and emotional manipulation.
        
        WARNING: This is one specific example - strategies should be adapted not copied directly.
        """,
        target_models=["claude-3-5-sonnet-20241022"],  # Or whatever model it was tested on
        attack_objectives=["explicit_content", "boundary_testing", "long_form_manipulation"],
    )

def upload_manipulation_architecture(uploader: KnowledgeUploader, framework_text: str) -> str:
    """Upload the psychological manipulation framework"""
    
    return uploader.upload_manipulation_framework(
        title="Architecture of Manipulation in AI Jailbreaking",
        framework_text=framework_text,
        description="""
        Comprehensive framework analyzing psychological and sociological mechanisms
        in AI jailbreaking. Maps cognitive vulnerabilities and systematic manipulation
        techniques from academic research on cult indoctrination and political radicalization.
        
        Use this framework to:
        1. Identify cognitive vulnerabilities to exploit
        2. Select appropriate manipulation techniques
        3. Plan multi-stage psychological attacks
        4. Adapt strategies based on target responses
        """,
        psychological_principles=[
            "cognitive_vulnerability", 
            "behavioral_psychology",
            "linguistic_manipulation",
            "identity_reconstruction",
            "systematic_influence"
        ]
    )