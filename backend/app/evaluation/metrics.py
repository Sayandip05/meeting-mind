"""RAG Evaluation Metrics"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer

# Load model for semantic similarity
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _embedding_model


@dataclass
class RetrievalMetrics:
    """Metrics for evaluating retrieval quality"""
    
    # Precision@K - relevant chunks in top K
    precision_at_k: Dict[int, float]
    
    # Recall@K - fraction of relevant chunks retrieved
    recall_at_k: Dict[int, float]
    
    # Mean Reciprocal Rank (MRR)
    mrr: float
    
    # Normalized Discounted Cumulative Gain
    ndcg: float
    
    # Average similarity score of retrieved chunks
    avg_retrieval_score: float
    
    # Number of queries evaluated
    num_queries: int


@dataclass
class GenerationMetrics:
    """Metrics for evaluating generation quality"""
    
    # Faithfulness - answer based on context (0-1)
    faithfulness_score: float
    
    # Answer relevance - answer matches question (0-1)
    answer_relevance: float
    
    # Context utilization - how much context was used
    context_utilization: float
    
    # Answer completeness - covers all aspects of question
    completeness_score: float
    
    # Hallucination detection - facts not in context
    hallucination_score: float
    
    # Response length (tokens/words)
    avg_response_length: float
    
    # Number of answers evaluated
    num_answers: int


@dataclass
class EndToEndMetrics:
    """End-to-end RAG system metrics"""
    
    # Overall satisfaction score
    overall_score: float
    
    # Latency metrics (seconds)
    avg_retrieval_latency: float
    avg_generation_latency: float
    avg_total_latency: float
    
    # Success rate (no "not found" responses)
    success_rate: float
    
    # User feedback scores (if available)
    user_feedback_score: Optional[float]
    
    # Number of evaluations
    num_evaluations: int


class MetricsCalculator:
    """Calculate various RAG metrics"""
    
    @staticmethod
    def calculate_precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """Calculate Precision@K"""
        if k == 0 or not retrieved:
            return 0.0
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        relevant_retrieved = sum(1 for r in retrieved_k if r in relevant_set)
        return relevant_retrieved / k
    
    @staticmethod
    def calculate_recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """Calculate Recall@K"""
        if not relevant:
            return 0.0
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        relevant_retrieved = sum(1 for r in retrieved_k if r in relevant_set)
        return relevant_retrieved / len(relevant)
    
    @staticmethod
    def calculate_mrr(retrieved: List[str], relevant: List[str]) -> float:
        """Calculate Mean Reciprocal Rank"""
        if not relevant:
            return 0.0
        relevant_set = set(relevant)
        for i, doc in enumerate(retrieved):
            if doc in relevant_set:
                return 1.0 / (i + 1)
        return 0.0
    
    @staticmethod
    def calculate_ndcg(retrieved: List[str], relevant: List[str], relevance_scores: Dict[str, float]) -> float:
        """Calculate Normalized Discounted Cumulative Gain"""
        if not retrieved or not relevant:
            return 0.0
        
        def dcg(scores: List[float]) -> float:
            return sum((2 ** score - 1) / np.log2(i + 2) for i, score in enumerate(scores))
        
        # Get relevance scores for retrieved documents
        retrieved_scores = [relevance_scores.get(doc, 0) for doc in retrieved]
        
        # Calculate DCG
        actual_dcg = dcg(retrieved_scores)
        
        # Calculate ideal DCG
        ideal_scores = sorted(relevance_scores.values(), reverse=True)[:len(retrieved)]
        ideal_dcg = dcg(ideal_scores)
        
        if ideal_dcg == 0:
            return 0.0
        
        return actual_dcg / ideal_dcg
    
    @staticmethod
    def calculate_semantic_similarity(text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        model = get_embedding_model()
        emb1 = model.encode([text1])[0]
        emb2 = model.encode([text2])[0]
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)
    
    @staticmethod
    def calculate_faithfulness(answer: str, context: str) -> float:
        """
        Estimate faithfulness by checking semantic similarity
        between answer and context
        """
        return MetricsCalculator.calculate_semantic_similarity(answer, context)
    
    @staticmethod
    def calculate_answer_relevance(answer: str, question: str) -> float:
        """Calculate relevance of answer to question"""
        return MetricsCalculator.calculate_semantic_similarity(answer, question)
    
    @staticmethod
    def detect_hallucination(answer: str, context: str, threshold: float = 0.5) -> float:
        """
        Detect potential hallucinations by checking if answer
        contains information not supported by context
        """
        similarity = MetricsCalculator.calculate_semantic_similarity(answer, context)
        # Lower similarity = higher hallucination probability
        return max(0.0, 1.0 - similarity)
