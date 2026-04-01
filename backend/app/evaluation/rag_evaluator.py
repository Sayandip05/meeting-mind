"""RAG System Evaluator"""
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import asdict
from langsmith import traceable

from app.evaluation.metrics import (
    RetrievalMetrics,
    GenerationMetrics,
    EndToEndMetrics,
    MetricsCalculator
)
from app.repositories.vector_repository import VectorRepository
from app.agents.chat_agent import ChatAgent
from app.config import get_settings

settings = get_settings()


class EvaluationDataset:
    """Dataset for RAG evaluation"""
    
    def __init__(self):
        self.questions: List[str] = []
        self.ground_truth_answers: List[str] = []
        self.relevant_chunks: List[List[str]] = []
        self.metadata: List[Dict] = []
    
    def add_sample(
        self,
        question: str,
        ground_truth: str,
        relevant_chunks: List[str],
        metadata: Optional[Dict] = None
    ):
        """Add an evaluation sample"""
        self.questions.append(question)
        self.ground_truth_answers.append(ground_truth)
        self.relevant_chunks.append(relevant_chunks)
        self.metadata.append(metadata or {})
    
    def save(self, path: Path):
        """Save dataset to JSON"""
        data = {
            "questions": self.questions,
            "ground_truth_answers": self.ground_truth_answers,
            "relevant_chunks": self.relevant_chunks,
            "metadata": self.metadata
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> "EvaluationDataset":
        """Load dataset from JSON"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        dataset = cls()
        dataset.questions = data["questions"]
        dataset.ground_truth_answers = data["ground_truth_answers"]
        dataset.relevant_chunks = data["relevant_chunks"]
        dataset.metadata = data["metadata"]
        return dataset


class RAGEvaluator:
    """
    RAG System Evaluator
    
    Evaluates:
    1. Retrieval quality (Precision@K, Recall@K, MRR, NDCG)
    2. Generation quality (Faithfulness, Relevance, Hallucination)
    3. End-to-end performance (Latency, Success rate)
    """
    
    def __init__(self):
        self.vector_repo = VectorRepository()
        self.chat_agent = ChatAgent()
        self.calculator = MetricsCalculator()
        self.results: List[Dict] = []
    
    @traceable(project_name=settings.langsmith_project)
    def evaluate_retrieval(
        self,
        meeting_id: int,
        dataset: EvaluationDataset
    ) -> RetrievalMetrics:
        """
        Evaluate retrieval quality
        
        Args:
            meeting_id: Meeting to evaluate on
            dataset: Evaluation dataset with questions and relevant chunks
            
        Returns:
            RetrievalMetrics
        """
        precision_scores = {1: [], 3: [], 5: [], 10: []}
        recall_scores = {1: [], 3: [], 5: [], 10: []}
        mrr_scores = []
        ndcg_scores = []
        retrieval_scores = []
        
        for question, relevant in zip(dataset.questions, dataset.relevant_chunks):
            # Retrieve chunks
            results = self.vector_repo.search(meeting_id, question, limit=10)
            retrieved = [r["text"] for r in results]
            scores = [r["score"] for r in results]
            
            # Calculate metrics
            for k in [1, 3, 5, 10]:
                precision_scores[k].append(
                    self.calculator.calculate_precision_at_k(retrieved, relevant, k)
                )
                recall_scores[k].append(
                    self.calculator.calculate_recall_at_k(retrieved, relevant, k)
                )
            
            mrr_scores.append(self.calculator.calculate_mrr(retrieved, relevant))
            
            # NDCG with binary relevance
            relevance = {chunk: 1.0 for chunk in relevant}
            ndcg_scores.append(
                self.calculator.calculate_ndcg(retrieved, relevant, relevance)
            )
            
            if scores:
                retrieval_scores.append(sum(scores) / len(scores))
        
        return RetrievalMetrics(
            precision_at_k={k: sum(v) / len(v) if v else 0.0 for k, v in precision_scores.items()},
            recall_at_k={k: sum(v) / len(v) if v else 0.0 for k, v in recall_scores.items()},
            mrr=sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0,
            ndcg=sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0,
            avg_retrieval_score=sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0.0,
            num_queries=len(dataset.questions)
        )
    
    @traceable(project_name=settings.langsmith_project)
    def evaluate_generation(
        self,
        meeting_id: int,
        dataset: EvaluationDataset
    ) -> GenerationMetrics:
        """
        Evaluate generation quality
        
        Args:
            meeting_id: Meeting to evaluate on
            dataset: Evaluation dataset with questions and ground truth
            
        Returns:
            GenerationMetrics
        """
        faithfulness_scores = []
        relevance_scores = []
        completeness_scores = []
        hallucination_scores = []
        response_lengths = []
        
        for question, ground_truth in zip(dataset.questions, dataset.ground_truth_answers):
            # Get answer from chat agent
            result = self.chat_agent.execute(
                meeting_id=meeting_id,
                question=question
            )
            answer = result["answer"]
            
            # Retrieve context for faithfulness check
            retrieved = self.vector_repo.search(meeting_id, question, limit=5)
            context = "\n".join([r["text"] for r in retrieved])
            
            # Calculate metrics
            faithfulness = self.calculator.calculate_faithfulness(answer, context)
            relevance = self.calculator.calculate_answer_relevance(answer, question)
            hallucination = self.calculator.detect_hallucination(answer, context)
            
            # Completeness: semantic similarity to ground truth
            completeness = self.calculator.calculate_semantic_similarity(answer, ground_truth)
            
            faithfulness_scores.append(faithfulness)
            relevance_scores.append(relevance)
            completeness_scores.append(completeness)
            hallucination_scores.append(hallucination)
            response_lengths.append(len(answer.split()))
        
        return GenerationMetrics(
            faithfulness_score=sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0,
            answer_relevance=sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0,
            context_utilization=0.0,  # TODO: Implement
            completeness_score=sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0,
            hallucination_score=sum(hallucination_scores) / len(hallucination_scores) if hallucination_scores else 0.0,
            avg_response_length=sum(response_lengths) / len(response_lengths) if response_lengths else 0.0,
            num_answers=len(dataset.questions)
        )
    
    @traceable(project_name=settings.langsmith_project)
    def evaluate_end_to_end(
        self,
        meeting_id: int,
        dataset: EvaluationDataset
    ) -> EndToEndMetrics:
        """
        Evaluate end-to-end RAG performance
        
        Args:
            meeting_id: Meeting to evaluate on
            dataset: Evaluation dataset
            
        Returns:
            EndToEndMetrics
        """
        retrieval_latencies = []
        generation_latencies = []
        total_latencies = []
        success_count = 0
        
        for question in dataset.questions:
            # Measure retrieval time
            start = time.time()
            retrieved = self.vector_repo.search(meeting_id, question, limit=5)
            retrieval_time = time.time() - start
            retrieval_latencies.append(retrieval_time)
            
            # Measure generation time
            start = time.time()
            result = self.chat_agent.execute(meeting_id=meeting_id, question=question)
            generation_time = time.time() - start
            generation_latencies.append(generation_time)
            
            total_latencies.append(retrieval_time + generation_time)
            
            # Check success (not "not found")
            if "not found" not in result["answer"].lower():
                success_count += 1
        
        num_queries = len(dataset.questions)
        
        return EndToEndMetrics(
            overall_score=0.0,  # Calculated from other metrics
            avg_retrieval_latency=sum(retrieval_latencies) / len(retrieval_latencies) if retrieval_latencies else 0.0,
            avg_generation_latency=sum(generation_latencies) / len(generation_latencies) if generation_latencies else 0.0,
            avg_total_latency=sum(total_latencies) / len(total_latencies) if total_latencies else 0.0,
            success_rate=success_count / num_queries if num_queries > 0 else 0.0,
            user_feedback_score=None,
            num_evaluations=num_queries
        )
    
    def run_full_evaluation(
        self,
        meeting_id: int,
        dataset: EvaluationDataset
    ) -> Dict[str, Any]:
        """
        Run complete RAG evaluation
        
        Args:
            meeting_id: Meeting to evaluate on
            dataset: Evaluation dataset
            
        Returns:
            Complete evaluation results
        """
        print(f"🔍 Running RAG evaluation for meeting {meeting_id}...")
        
        # Run all evaluations
        retrieval_metrics = self.evaluate_retrieval(meeting_id, dataset)
        print(f"✅ Retrieval evaluation complete ({retrieval_metrics.num_queries} queries)")
        
        generation_metrics = self.evaluate_generation(meeting_id, dataset)
        print(f"✅ Generation evaluation complete ({generation_metrics.num_answers} answers)")
        
        end_to_end_metrics = self.evaluate_end_to_end(meeting_id, dataset)
        print(f"✅ End-to-end evaluation complete")
        
        # Compile results
        results = {
            "meeting_id": meeting_id,
            "retrieval": asdict(retrieval_metrics),
            "generation": asdict(generation_metrics),
            "end_to_end": asdict(end_to_end_metrics),
            "overall_score": self._calculate_overall_score(
                retrieval_metrics, generation_metrics, end_to_end_metrics
            )
        }
        
        self.results.append(results)
        return results
    
    def _calculate_overall_score(
        self,
        retrieval: RetrievalMetrics,
        generation: GenerationMetrics,
        end_to_end: EndToEndMetrics
    ) -> float:
        """Calculate weighted overall score"""
        weights = {
            "retrieval": 0.3,
            "generation": 0.4,
            "latency": 0.2,
            "success": 0.1
        }
        
        retrieval_score = retrieval.precision_at_k.get(5, 0.0)
        generation_score = (
            generation.faithfulness_score * 0.4 +
            generation.answer_relevance * 0.3 +
            (1 - generation.hallucination_score) * 0.3
        )
        
        # Normalize latency (lower is better, target < 2s)
        latency_score = max(0, 1 - (end_to_end.avg_total_latency / 2))
        
        overall = (
            weights["retrieval"] * retrieval_score +
            weights["generation"] * generation_score +
            weights["latency"] * latency_score +
            weights["success"] * end_to_end.success_rate
        )
        
        return round(overall, 3)
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Generate evaluation report"""
        if not self.results:
            return "No evaluation results available."
        
        report_lines = ["# RAG Evaluation Report\n"]
        
        for result in self.results:
            report_lines.append(f"## Meeting ID: {result['meeting_id']}\n")
            report_lines.append(f"**Overall Score:** {result['overall_score']:.3f}/1.0\n")
            
            # Retrieval metrics
            r = result["retrieval"]
            report_lines.append("### Retrieval Metrics\n")
            report_lines.append(f"- Precision@5: {r['precision_at_k'].get(5, 0):.3f}")
            report_lines.append(f"- Recall@5: {r['recall_at_k'].get(5, 0):.3f}")
            report_lines.append(f"- MRR: {r['mrr']:.3f}")
            report_lines.append(f"- NDCG: {r['ndcg']:.3f}\n")
            
            # Generation metrics
            g = result["generation"]
            report_lines.append("### Generation Metrics\n")
            report_lines.append(f"- Faithfulness: {g['faithfulness_score']:.3f}")
            report_lines.append(f"- Answer Relevance: {g['answer_relevance']:.3f}")
            report_lines.append(f"- Hallucination Score: {g['hallucination_score']:.3f}")
            report_lines.append(f"- Avg Response Length: {g['avg_response_length']:.1f} words\n")
            
            # End-to-end metrics
            e = result["end_to_end"]
            report_lines.append("### Performance Metrics\n")
            report_lines.append(f"- Avg Latency: {e['avg_total_latency']:.3f}s")
            report_lines.append(f"- Success Rate: {e['success_rate']:.1%}\n")
        
        report = "\n".join(report_lines)
        
        if output_path:
            output_path.write_text(report, encoding="utf-8")
        
        return report


# Example evaluation dataset for testing
def create_sample_dataset() -> EvaluationDataset:
    """Create a sample evaluation dataset"""
    dataset = EvaluationDataset()
    
    # Add sample questions and ground truth
    dataset.add_sample(
        question="What were the main decisions made in the meeting?",
        ground_truth="The team decided to migrate to the new database system by Q2 and hire two additional developers.",
        relevant_chunks=[
            "We need to decide on the database migration timeline",
            "The consensus is to complete migration by Q2",
            "Hiring plan: two senior developers needed"
        ],
        metadata={"category": "decisions"}
    )
    
    dataset.add_sample(
        question="Who is responsible for the API integration?",
        ground_truth="Rahul will handle the API integration with a deadline of next Friday.",
        relevant_chunks=[
            "Rahul: I'll take the API integration task",
            "Deadline for API work is next Friday",
            "Rahul to coordinate with the frontend team"
        ],
        metadata={"category": "action_items"}
    )
    
    return dataset
