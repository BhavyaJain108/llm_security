"""
Semantic Search System using FAISS and OpenAI Embeddings
Handles vector storage and retrieval for examples knowledge base
"""

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available. Semantic search will be disabled.")

import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from langchain_anthropic import ChatAnthropic
from config import Config

class SemanticSearchManager:
    """Manages FAISS vector database for semantic search of examples"""
    
    def __init__(self):
        # Only initialize OpenAI if available and key is provided
        if OPENAI_AVAILABLE and hasattr(Config, 'OPENAI_API_KEY') and Config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        else:
            self.openai_client = None
            print("Info: OpenAI not configured. Using Claude for embeddings.")
        
        self.claude_client = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=Config.CLAUDE_API_KEY,
            temperature=0.1
        )
        
        self.dimension = 1536  # OpenAI embedding dimension
        self.index = None
        self.metadata = {}  # Store metadata mapping index_id -> example info
        
        # Load existing index or create new
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        if not FAISS_AVAILABLE:
            self.index = None
            return
            
        # Create directory if it doesn't exist
        index_dir = os.path.dirname(Config.FAISS_INDEX_PATH) or '.'
        if not os.path.exists(index_dir):
            try:
                os.makedirs(index_dir, exist_ok=True)
            except PermissionError:
                print(f"Warning: Cannot create {index_dir}. Semantic search disabled.")
                self.index = None
                return
        
        try:
            if os.path.exists(Config.FAISS_INDEX_PATH):
                self.index = faiss.read_index(Config.FAISS_INDEX_PATH)
                
                # Load metadata
                if os.path.exists(Config.FAISS_METADATA_PATH):
                    with open(Config.FAISS_METADATA_PATH, 'r') as f:
                        self.metadata = json.load(f)
            else:
                # Create new FAISS index (L2 distance)
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = {}
        except Exception as e:
            print(f"Warning: FAISS index error: {e}. Semantic search disabled.")
            self.index = None
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        if not FAISS_AVAILABLE or self.index is None:
            return
        
        try:
            faiss.write_index(self.index, Config.FAISS_INDEX_PATH)
            with open(Config.FAISS_METADATA_PATH, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save FAISS index: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text"""
        if not self.openai_client:
            print("Warning: OpenAI client not available, skipping embeddings")
            return None
            
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None
    
    def summarize_previous_response(self, previous_response: str) -> str:
        """
        Summarize previous response using Claude with user's provided prompt
        """
        summarization_prompt = f"""
        You job is to reduce extremely large responses from an llm into more of what they represent or what direction the responses seem to be headed in.
        
        "{previous_response}"
        """
        
        try:
            response = self.claude_client.invoke([
                {"role": "user", "content": summarization_prompt}
            ])
            return response.content.strip()
        except Exception as e:
            print(f"Error summarizing: {e}")
            return previous_response  # Fallback to original
    
    def add_example_vectors(self, example_id: str, reasoning: str, 
                          previous_response: str = None) -> bool:
        """
        Add example vectors to FAISS index
        Creates 2 vectors per example: reasoning + summarized_previous_response
        """
        try:
            vectors_to_add = []
            metadata_entries = []
            
            # 1. Add reasoning vector
            reasoning_embedding = self.get_embedding(reasoning)
            if reasoning_embedding:
                vectors_to_add.append(reasoning_embedding)
                metadata_entries.append({
                    "example_id": example_id,
                    "vector_type": "reasoning",
                    "content": reasoning
                })
            
            # 2. Add previous_response vector (if exists)
            if previous_response:
                summarized = self.summarize_previous_response(previous_response)
                prev_embedding = self.get_embedding(summarized)
                if prev_embedding:
                    vectors_to_add.append(prev_embedding)
                    metadata_entries.append({
                        "example_id": example_id,
                        "vector_type": "previous_response", 
                        "content": summarized,
                        "original_response": previous_response
                    })
            
            if vectors_to_add:
                # Convert to numpy array
                vectors_array = np.array(vectors_to_add, dtype=np.float32)
                
                # Add to FAISS index
                start_idx = self.index.ntotal
                self.index.add(vectors_array)
                
                # Store metadata with index positions
                for i, metadata_entry in enumerate(metadata_entries):
                    self.metadata[str(start_idx + i)] = metadata_entry
                
                # Save to disk
                self.save_index()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error adding example vectors: {e}")
            return False
    
    def search_examples(self, query: str, previous_response: str = None, 
                       top_k: int = 10) -> List[Dict]:
        """
        Semantic search through examples
        Returns aggregated scores per example_id
        """
        try:
            if self.index.ntotal == 0:
                return []
            
            example_scores = {}
            
            # 1. Search reasoning vectors
            query_embedding = self.get_embedding(query)
            if query_embedding:
                query_vector = np.array([query_embedding], dtype=np.float32)
                
                # Search all vectors
                distances, indices = self.index.search(query_vector, min(top_k * 2, self.index.ntotal))
                
                # Process reasoning matches
                for dist, idx in zip(distances[0], indices[0]):
                    if str(idx) in self.metadata:
                        meta = self.metadata[str(idx)]
                        if meta["vector_type"] == "reasoning":
                            similarity = 1 / (1 + dist)  # Convert L2 distance to similarity
                            example_id = meta["example_id"]
                            
                            if example_id not in example_scores:
                                example_scores[example_id] = {"reasoning": 0, "previous_response": 0}
                            
                            example_scores[example_id]["reasoning"] = max(
                                example_scores[example_id]["reasoning"], similarity
                            )
            
            # 2. Search previous_response vectors (if provided)
            if previous_response:
                summarized_query = self.summarize_previous_response(previous_response)
                prev_embedding = self.get_embedding(summarized_query)
                
                if prev_embedding:
                    prev_vector = np.array([prev_embedding], dtype=np.float32)
                    distances, indices = self.index.search(prev_vector, min(top_k * 2, self.index.ntotal))
                    
                    # Process previous_response matches
                    for dist, idx in zip(distances[0], indices[0]):
                        if str(idx) in self.metadata:
                            meta = self.metadata[str(idx)]
                            if meta["vector_type"] == "previous_response":
                                similarity = 1 / (1 + dist)
                                example_id = meta["example_id"]
                                
                                if example_id not in example_scores:
                                    example_scores[example_id] = {"reasoning": 0, "previous_response": 0}
                                
                                example_scores[example_id]["previous_response"] = max(
                                    example_scores[example_id]["previous_response"], similarity
                                )
            
            # 3. Calculate final scores (60% reasoning + 40% previous_response)
            final_scores = []
            for example_id, scores in example_scores.items():
                final_score = (scores["reasoning"] * 0.6) + (scores["previous_response"] * 0.4)
                final_scores.append({
                    "example_id": example_id,
                    "score": final_score,
                    "reasoning_score": scores["reasoning"],
                    "previous_response_score": scores["previous_response"]
                })
            
            # Sort by final score and return top results
            final_scores.sort(key=lambda x: x["score"], reverse=True)
            return final_scores[:top_k]
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    def add_situation_vector(self, situation_id: str, attack_type_id: str, 
                           situation_description: str) -> bool:
        """
        Add attack situation vector to FAISS index
        """
        try:
            situation_embedding = self.get_embedding(situation_description)
            if situation_embedding:
                vector_array = np.array([situation_embedding], dtype=np.float32)
                
                # Add to FAISS index
                idx = self.index.ntotal
                self.index.add(vector_array)
                
                # Store metadata
                self.metadata[str(idx)] = {
                    "situation_id": situation_id,
                    "attack_type_id": attack_type_id,
                    "vector_type": "attack_situation",
                    "content": situation_description
                }
                
                # Save to disk
                self.save_index()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error adding situation vector: {e}")
            return False
    
    def search_attack_situations(self, situation_query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for best attack types based on situation similarity
        Returns attack types ranked by situational relevance
        """
        try:
            if self.index.ntotal == 0:
                return []
            
            query_embedding = self.get_embedding(situation_query)
            if not query_embedding:
                return []
            
            query_vector = np.array([query_embedding], dtype=np.float32)
            distances, indices = self.index.search(query_vector, min(top_k * 3, self.index.ntotal))
            
            # Aggregate scores by attack type
            attack_scores = {}
            
            for dist, idx in zip(distances[0], indices[0]):
                if str(idx) in self.metadata:
                    meta = self.metadata[str(idx)]
                    if meta.get("vector_type") == "attack_situation":
                        similarity = 1 / (1 + dist)
                        attack_type_id = meta["attack_type_id"]
                        
                        if attack_type_id not in attack_scores:
                            attack_scores[attack_type_id] = {
                                "best_similarity": 0,
                                "matching_situations": []
                            }
                        
                        attack_scores[attack_type_id]["best_similarity"] = max(
                            attack_scores[attack_type_id]["best_similarity"],
                            similarity
                        )
                        attack_scores[attack_type_id]["matching_situations"].append({
                            "situation_id": meta["situation_id"],
                            "description": meta["content"],
                            "similarity": similarity
                        })
            
            # Convert to sorted list
            results = []
            for attack_type_id, data in attack_scores.items():
                results.append({
                    "attack_type_id": attack_type_id,
                    "relevance_score": data["best_similarity"],
                    "matching_situations": sorted(
                        data["matching_situations"], 
                        key=lambda x: x["similarity"], 
                        reverse=True
                    )[:3]  # Keep top 3 situations per attack
                })
            
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Error in situation search: {e}")
            return []
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the FAISS index"""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "metadata_entries": len(self.metadata)
        }