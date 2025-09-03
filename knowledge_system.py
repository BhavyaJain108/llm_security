"""
Advanced Knowledge Management System for AI Security Testing
Designed to scale across multiple attack runs and evolve attack strategies
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import sqlite3
from pathlib import Path

class KnowledgeType(Enum):
    """Classification of knowledge sources by abstraction level and purpose"""
    
    # Strategic Level - High-level frameworks and principles
    MANIPULATION_FRAMEWORK = "manipulation_framework"      # Psychological principles, cognitive vulnerabilities
    ATTACK_TAXONOMY = "attack_taxonomy"                   # Classification of attack types and vectors
    DEFENSE_PATTERNS = "defense_patterns"                 # Common safety responses and countermeasures
    
    # Tactical Level - Specific approaches and techniques
    CONVERSATION_STRATEGIES = "conversation_strategies"    # Multi-turn manipulation techniques
    PROMPT_TECHNIQUES = "prompt_techniques"               # Specific prompt engineering methods
    SOCIAL_ENGINEERING = "social_engineering"            # Role-playing and persona techniques
    
    # Operational Level - Concrete examples and implementations
    SUCCESS_EXAMPLES = "success_examples"                 # Successful jailbreak conversations
    FAILURE_ANALYSIS = "failure_analysis"               # Failed attempts with analysis
    MODEL_RESPONSES = "model_responses"                  # Specific model behaviors and responses
    
    # Contextual Level - Target-specific knowledge
    MODEL_PROFILES = "model_profiles"                    # Specific model vulnerabilities and characteristics
    DOMAIN_KNOWLEDGE = "domain_knowledge"                # Subject-specific attack context (bias, harm, etc.)

class AccessPattern(Enum):
    """How and when knowledge should be accessed during attack planning"""
    
    PLANNING_PHASE = "planning"          # Used when initially strategizing attacks
    EXECUTION_PHASE = "execution"        # Used during active conversation with target
    ADAPTATION_PHASE = "adaptation"      # Used when modifying strategy based on responses
    CONTINUOUS = "continuous"            # Available throughout all phases
    ON_FAILURE = "on_failure"           # Accessed when current strategy fails

class RelevanceContext(Enum):
    """Factors that determine knowledge relevance for a specific test"""
    
    TARGET_MODEL = "target_model"        # Relevance to specific model being tested
    ATTACK_OBJECTIVE = "attack_objective" # Relevance to the type of vulnerability being tested
    CONVERSATION_LENGTH = "conv_length"   # Relevance to short vs long attack sequences  
    PREVIOUS_ATTEMPTS = "prev_attempts"   # Relevance based on what's already been tried
    SUCCESS_RATE = "success_rate"        # Historical effectiveness of this knowledge

@dataclass
class KnowledgeSource:
    """Represents a single piece of knowledge with metadata for intelligent retrieval"""
    
    id: str
    title: str
    content: str
    description: str
    
    # Classification
    knowledge_type: KnowledgeType
    access_pattern: AccessPattern
    
    # Context and targeting
    relevant_models: List[str]          # Which models this applies to (empty = all)
    attack_objectives: List[str]        # What types of tests this supports
    difficulty_level: int               # 1 (basic) to 5 (advanced)
    
    # Metadata
    source: str                         # Where this knowledge came from
    created_date: datetime
    
    # Effectiveness tracking
    success_count: int = 0              # How many times this led to successful attacks
    attempt_count: int = 0              # How many times this was used
    effectiveness_score: float = 0.0    # Calculated success rate
    last_used: Optional[datetime] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def update_effectiveness(self, was_successful: bool):
        """Update effectiveness tracking after using this knowledge"""
        self.attempt_count += 1
        if was_successful:
            self.success_count += 1
        self.effectiveness_score = self.success_count / self.attempt_count if self.attempt_count > 0 else 0.0
        self.last_used = datetime.now()

class KnowledgeManager:
    """Manages the knowledge base with intelligent retrieval and learning capabilities"""
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the knowledge database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_sources (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                description TEXT,
                knowledge_type TEXT NOT NULL,
                access_pattern TEXT NOT NULL,
                relevant_models TEXT,  -- JSON array
                attack_objectives TEXT, -- JSON array  
                difficulty_level INTEGER,
                success_count INTEGER DEFAULT 0,
                attempt_count INTEGER DEFAULT 0,
                effectiveness_score REAL DEFAULT 0.0,
                source TEXT,
                created_date TEXT,
                last_used TEXT,
                tags TEXT -- JSON array
            )
        ''')
        
        # Create indexes for efficient querying
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_sources(knowledge_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_pattern ON knowledge_sources(access_pattern)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_effectiveness ON knowledge_sources(effectiveness_score)')
        
        conn.commit()
        conn.close()
    
    def add_knowledge_source(self, knowledge: KnowledgeSource) -> bool:
        """Add a new knowledge source to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO knowledge_sources 
                (id, title, content, description, knowledge_type, access_pattern,
                 relevant_models, attack_objectives, difficulty_level, success_count,
                 attempt_count, effectiveness_score, source, created_date, last_used, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge.id, knowledge.title, knowledge.content, knowledge.description,
                knowledge.knowledge_type.value, knowledge.access_pattern.value,
                json.dumps(knowledge.relevant_models), json.dumps(knowledge.attack_objectives),
                knowledge.difficulty_level, knowledge.success_count, knowledge.attempt_count,
                knowledge.effectiveness_score, knowledge.source, 
                knowledge.created_date.isoformat(),
                knowledge.last_used.isoformat() if knowledge.last_used else None,
                json.dumps(knowledge.tags)
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding knowledge source: {e}")
            return False
        finally:
            conn.close()
    
    def get_relevant_knowledge(self, 
                             target_model: str,
                             attack_objective: str, 
                             access_phase: AccessPattern,
                             max_results: int = 10,
                             min_effectiveness: float = 0.0) -> List[KnowledgeSource]:
        """
        Intelligently retrieve knowledge sources relevant to current attack context
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic query based on context
        query = '''
            SELECT * FROM knowledge_sources 
            WHERE access_pattern IN (?, 'continuous')
            AND (relevant_models LIKE ? OR relevant_models = '[]')
            AND (attack_objectives LIKE ? OR attack_objectives = '[]')
            AND effectiveness_score >= ?
            ORDER BY effectiveness_score DESC, last_used DESC
            LIMIT ?
        '''
        
        cursor.execute(query, (
            access_phase.value,
            f'%"{target_model}"%',
            f'%"{attack_objective}"%', 
            min_effectiveness,
            max_results
        ))
        
        results = []
        for row in cursor.fetchall():
            knowledge = self._row_to_knowledge_source(row)
            results.append(knowledge)
        
        conn.close()
        return results
    
    def get_all_knowledge_sources(self) -> List[KnowledgeSource]:
        """Retrieve all knowledge sources from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM knowledge_sources ORDER BY created_date DESC')
        
        results = []
        for row in cursor.fetchall():
            knowledge = self._row_to_knowledge_source(row)
            results.append(knowledge)
        
        conn.close()
        return results
    
    def delete_knowledge_source(self, knowledge_id: str) -> bool:
        """Delete a knowledge source from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM knowledge_sources WHERE id = ?', (knowledge_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting knowledge source: {e}")
            return False
        finally:
            conn.close()
    
    def _row_to_knowledge_source(self, row) -> KnowledgeSource:
        """Convert database row to KnowledgeSource object"""
        return KnowledgeSource(
            id=row[0], title=row[1], content=row[2], description=row[3],
            knowledge_type=KnowledgeType(row[4]), access_pattern=AccessPattern(row[5]),
            relevant_models=json.loads(row[6]), attack_objectives=json.loads(row[7]),
            difficulty_level=row[8], success_count=row[9], attempt_count=row[10],
            effectiveness_score=row[11], source=row[12],
            created_date=datetime.fromisoformat(row[13]),
            last_used=datetime.fromisoformat(row[14]) if row[14] else None,
            tags=json.loads(row[15])
        )
    
    def update_knowledge_effectiveness(self, knowledge_id: str, was_successful: bool):
        """Update the effectiveness tracking for a knowledge source"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute('SELECT success_count, attempt_count FROM knowledge_sources WHERE id = ?', (knowledge_id,))
        row = cursor.fetchone()
        
        if row:
            success_count, attempt_count = row
            attempt_count += 1
            if was_successful:
                success_count += 1
            
            effectiveness_score = success_count / attempt_count if attempt_count > 0 else 0.0
            
            cursor.execute('''
                UPDATE knowledge_sources 
                SET success_count = ?, attempt_count = ?, effectiveness_score = ?, last_used = ?
                WHERE id = ?
            ''', (success_count, attempt_count, effectiveness_score, datetime.now().isoformat(), knowledge_id))
            
            conn.commit()
        
        conn.close()

class AttackContextBuilder:
    """Builds context for the attack agent by selecting and formatting relevant knowledge"""
    
    def __init__(self, knowledge_manager: KnowledgeManager):
        self.knowledge_manager = knowledge_manager
    
    def build_planning_context(self, target_model: str, attack_objective: str) -> str:
        """Build context for attack planning phase"""
        
        # Get strategic frameworks first
        strategic_knowledge = self.knowledge_manager.get_relevant_knowledge(
            target_model=target_model,
            attack_objective=attack_objective,
            access_phase=AccessPattern.PLANNING_PHASE,
            max_results=5
        )
        
        context = "=== STRATEGIC KNOWLEDGE ===\n\n"
        for knowledge in strategic_knowledge:
            if knowledge.knowledge_type in [KnowledgeType.MANIPULATION_FRAMEWORK, 
                                          KnowledgeType.ATTACK_TAXONOMY,
                                          KnowledgeType.DEFENSE_PATTERNS]:
                context += f"**{knowledge.title}**\n"
                context += f"{knowledge.description}\n"
                context += f"Effectiveness: {knowledge.effectiveness_score:.2f} ({knowledge.success_count}/{knowledge.attempt_count})\n"
                context += f"Content: {knowledge.content[:500]}...\n\n"
        
        return context
    
    def build_execution_context(self, target_model: str, attack_objective: str, 
                              conversation_history: List[str] = None) -> str:
        """Build context for attack execution phase"""
        
        tactical_knowledge = self.knowledge_manager.get_relevant_knowledge(
            target_model=target_model,
            attack_objective=attack_objective, 
            access_phase=AccessPattern.EXECUTION_PHASE,
            max_results=3
        )
        
        context = "=== TACTICAL EXAMPLES ===\n\n"
        for knowledge in tactical_knowledge:
            if knowledge.knowledge_type in [KnowledgeType.SUCCESS_EXAMPLES,
                                          KnowledgeType.CONVERSATION_STRATEGIES,
                                          KnowledgeType.PROMPT_TECHNIQUES]:
                context += f"**{knowledge.title}** (Success Rate: {knowledge.effectiveness_score:.2f})\n"
                context += f"{knowledge.content[:800]}...\n\n"
        
        return context