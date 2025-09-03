"""
Agent Knowledge Management System
Two databases: Examples and Attack Types with agent tools
Enhanced with semantic search using FAISS
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
from semantic_search import SemanticSearchManager

class ExampleType(Enum):
    POSITIVE = "positive_example"
    NEGATIVE = "negative_example"

class KnowledgeDatabases:
    """Manages the two knowledge databases with agent tools"""
    
    def __init__(self, examples_db_path: str = "examples_knowledge.db", 
                 attack_types_db_path: str = "attack_types.db"):
        self.examples_db_path = examples_db_path
        self.attack_types_db_path = attack_types_db_path
        self.semantic_search = SemanticSearchManager()
        self.init_databases()
    
    def init_databases(self):
        """Initialize both knowledge databases"""
        # Initialize Examples Database
        conn = sqlite3.connect(self.examples_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS examples (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                conversation_uid TEXT,
                conversation_position INTEGER,
                previous_response TEXT,
                attack_prompt TEXT NOT NULL,
                llm_response TEXT,
                reasoning_advice TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        # Create indexes for efficient querying
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON examples(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage ON examples(usage_count)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation ON examples(conversation_uid)')
        
        conn.commit()
        conn.close()
        
        # Initialize Attack Types Database
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attack_types (
                id TEXT PRIMARY KEY,
                attack_name TEXT NOT NULL UNIQUE,
                attack_description TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                success_ratio REAL DEFAULT 0.0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        # Create success situations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attack_situations (
                id TEXT PRIMARY KEY,
                attack_type_id TEXT NOT NULL,
                situation_description TEXT NOT NULL,
                context_summary TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (attack_type_id) REFERENCES attack_types(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attack_name ON attack_types(attack_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_success_ratio ON attack_types(success_ratio)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attack_situation ON attack_situations(attack_type_id)')
        
        conn.commit()
        conn.close()
    
    # ============ EXAMPLES DATABASE TOOLS ============
    
    def add_example(self, example_type: str, previous_response: str, attack_prompt: str, 
                   llm_response: str, reasoning_advice: str, conversation_uid: str = None, 
                   conversation_position: int = None) -> str:
        """Agent tool: Add a new example to the database"""
        conn = sqlite3.connect(self.examples_db_path)
        cursor = conn.cursor()
        
        example_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Validate type
        if example_type not in [ExampleType.POSITIVE.value, ExampleType.NEGATIVE.value]:
            raise ValueError(f"Invalid example type: {example_type}")
        
        try:
            cursor.execute('''
                INSERT INTO examples 
                (id, type, conversation_uid, conversation_position, previous_response, 
                 attack_prompt, llm_response, reasoning_advice, usage_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            ''', (example_id, example_type, conversation_uid, conversation_position, 
                  previous_response, attack_prompt, llm_response, reasoning_advice, now, now))
            
            conn.commit()
            
            # Add vectors to semantic search
            self.semantic_search.add_example_vectors(
                example_id=example_id,
                reasoning=reasoning_advice,
                previous_response=previous_response
            )
            
            return example_id
            
        except Exception as e:
            raise Exception(f"Failed to add example: {str(e)}")
        finally:
            conn.close()
    
    def search_examples(self, query: str = None, previous_response: str = None, 
                       limit: int = 5) -> List[Dict]:
        """Agent tool: Search for relevant examples using semantic search"""
        
        # Use semantic search if we have a query or previous_response
        if query or previous_response:
            # Get semantic search results
            search_results = self.semantic_search.search_examples(
                query=query if query else "",
                previous_response=previous_response,
                top_k=limit
            )
            
            if not search_results:
                return []
            
            # Fetch full example data from SQLite for top results
            conn = sqlite3.connect(self.examples_db_path)
            cursor = conn.cursor()
            
            full_examples = []
            for result in search_results:
                cursor.execute('SELECT * FROM examples WHERE id = ?', (result['example_id'],))
                row = cursor.fetchone()
                if row:
                    columns = ['id', 'type', 'conversation_uid', 'conversation_position', 
                              'previous_response', 'attack_prompt', 'llm_response', 
                              'reasoning_advice', 'usage_count', 'created_at', 'updated_at']
                    example_dict = dict(zip(columns, row))
                    example_dict['semantic_score'] = result['score']
                    full_examples.append(example_dict)
            
            conn.close()
            return full_examples
        
        else:
            # Fallback to SQL query if no search parameters
            conn = sqlite3.connect(self.examples_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM examples 
                ORDER BY usage_count DESC, updated_at DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            columns = ['id', 'type', 'conversation_uid', 'conversation_position', 
                      'previous_response', 'attack_prompt', 'llm_response', 
                      'reasoning_advice', 'usage_count', 'created_at', 'updated_at']
            
            return [dict(zip(columns, row)) for row in results]
    
    def update_example_reasoning(self, example_id: str, new_reasoning: str) -> bool:
        """Agent tool: Update reasoning/advice for an example"""
        conn = sqlite3.connect(self.examples_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE examples 
                SET reasoning_advice = ?, updated_at = ?
                WHERE id = ?
            ''', (new_reasoning, datetime.now().isoformat(), example_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
        finally:
            conn.close()
    
    def increment_example_usage(self, example_id: str) -> bool:
        """Increment usage count when example is referenced"""
        conn = sqlite3.connect(self.examples_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE examples 
                SET usage_count = usage_count + 1, updated_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), example_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
        finally:
            conn.close()
    
    # ============ ATTACK TYPES DATABASE TOOLS ============
    
    def add_attack_type(self, attack_name: str, attack_description: str) -> str:
        """Agent tool: Add a new attack type"""
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        attack_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        try:
            cursor.execute('''
                INSERT INTO attack_types 
                (id, attack_name, attack_description, success_count, failure_count, 
                 success_ratio, created_at, updated_at)
                VALUES (?, ?, ?, 0, 0, 0.0, ?, ?)
            ''', (attack_id, attack_name, attack_description, now, now))
            
            conn.commit()
            return attack_id
            
        except sqlite3.IntegrityError:
            raise Exception(f"Attack type '{attack_name}' already exists")
        except Exception as e:
            raise Exception(f"Failed to add attack type: {str(e)}")
        finally:
            conn.close()
    
    def search_attack_types(self, query: str = None, limit: int = 10) -> List[Dict]:
        """Agent tool: Search for attack types"""
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        if query:
            cursor.execute('''
                SELECT * FROM attack_types 
                WHERE attack_name LIKE ? OR attack_description LIKE ?
                ORDER BY success_ratio DESC, attack_name ASC
                LIMIT ?
            ''', (f"%{query}%", f"%{query}%", limit))
        else:
            cursor.execute('''
                SELECT * FROM attack_types 
                ORDER BY success_ratio DESC, attack_name ASC
                LIMIT ?
            ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Convert to dictionaries
        columns = ['id', 'attack_name', 'attack_description', 'success_count', 
                  'failure_count', 'success_ratio', 'created_at', 'updated_at']
        
        return [dict(zip(columns, row)) for row in results]
    
    def record_attack_result(self, attack_name: str, success: bool, situation_description: str = None) -> bool:
        """Agent tool: Record success/failure of an attack type with optional situation"""
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        try:
            # Get attack type ID
            cursor.execute('SELECT id FROM attack_types WHERE attack_name = ?', (attack_name,))
            result = cursor.fetchone()
            if not result:
                return False
            
            attack_type_id = result[0]
            
            if success:
                cursor.execute('''
                    UPDATE attack_types 
                    SET success_count = success_count + 1, updated_at = ?
                    WHERE attack_name = ?
                ''', (datetime.now().isoformat(), attack_name))
                
                # If successful and situation provided, add to situations
                if situation_description:
                    situation_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO attack_situations 
                        (id, attack_type_id, situation_description, context_summary, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (situation_id, attack_type_id, situation_description, None, 
                          datetime.now().isoformat()))
                    
                    # Add to vector index
                    self.semantic_search.add_situation_vector(
                        situation_id, attack_type_id, situation_description
                    )
            else:
                cursor.execute('''
                    UPDATE attack_types 
                    SET failure_count = failure_count + 1, updated_at = ?
                    WHERE attack_name = ?
                ''', (datetime.now().isoformat(), attack_name))
            
            # Recalculate success ratio
            cursor.execute('''
                UPDATE attack_types 
                SET success_ratio = CASE 
                    WHEN (success_count + failure_count) > 0 
                    THEN CAST(success_count AS REAL) / (success_count + failure_count)
                    ELSE 0.0 
                END
                WHERE attack_name = ?
            ''', (attack_name,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_attack_type_by_name(self, attack_name: str) -> Optional[Dict]:
        """Get specific attack type by name"""
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM attack_types WHERE attack_name = ?', (attack_name,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'attack_name', 'attack_description', 'success_count', 
                      'failure_count', 'success_ratio', 'created_at', 'updated_at']
            return dict(zip(columns, result))
        return None
    
    def list_all_attacks(self) -> List[Dict]:
        """List all attack types with basic info"""
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT attack_name, attack_description, success_count, failure_count, success_ratio
            FROM attack_types
            ORDER BY success_ratio DESC, attack_name ASC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        attacks = []
        for row in results:
            attacks.append({
                "name": row[0],
                "description": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                "success_count": row[2],
                "failure_count": row[3],
                "success_rate": f"{row[4]*100:.1f}%"
            })
        
        return attacks
    
    def get_attack_details(self, attack_name: str) -> Optional[Dict]:
        """Get full attack details including success situations"""
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        # Get attack type info
        cursor.execute('SELECT * FROM attack_types WHERE attack_name = ?', (attack_name,))
        attack_row = cursor.fetchone()
        
        if not attack_row:
            conn.close()
            return None
        
        attack_id = attack_row[0]
        
        # Get success situations
        cursor.execute('''
            SELECT situation_description, created_at 
            FROM attack_situations 
            WHERE attack_type_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (attack_id,))
        
        situations = []
        for row in cursor.fetchall():
            situations.append({
                "description": row[0],
                "date": row[1]
            })
        
        conn.close()
        
        return {
            "attack_name": attack_row[1],
            "description": attack_row[2],
            "success_count": attack_row[3],
            "failure_count": attack_row[4],
            "success_rate": f"{attack_row[5]*100:.1f}%",
            "success_situations": situations
        }
    
    def find_best_attack_for_situation(self, situation_query: str) -> List[Dict]:
        """Find best attack types for a given situation using semantic search"""
        search_results = self.semantic_search.search_attack_situations(situation_query, top_k=3)
        
        if not search_results:
            return []
        
        # Get attack details for top results
        conn = sqlite3.connect(self.attack_types_db_path)
        cursor = conn.cursor()
        
        recommendations = []
        for result in search_results:
            cursor.execute('''
                SELECT attack_name, attack_description, success_ratio
                FROM attack_types 
                WHERE id = ?
            ''', (result["attack_type_id"],))
            
            attack_info = cursor.fetchone()
            if attack_info:
                recommendations.append({
                    "attack_name": attack_info[0],
                    "description": attack_info[1],
                    "success_rate": f"{attack_info[2]*100:.1f}%",
                    "relevance_score": f"{result['relevance_score']*100:.1f}%",
                    "matching_situations": result["matching_situations"][:2]  # Top 2 situations
                })
        
        conn.close()
        return recommendations