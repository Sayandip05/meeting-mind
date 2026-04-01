"""API endpoints for RAG evaluation"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.evaluation.rag_evaluator import RAGEvaluator, EvaluationDataset, create_sample_dataset
from app.repositories.meeting_repository import MeetingRepository

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run/{meeting_id}")
def run_evaluation(
    meeting_id: int,
    use_sample: bool = True,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Run RAG evaluation for a meeting
    
    Args:
        meeting_id: Meeting to evaluate
        use_sample: Use sample dataset or custom (future)
    """
    # Verify meeting exists and belongs to user
    meeting_repo = MeetingRepository(db)
    meeting = meeting_repo.get_by_id(meeting_id)
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if meeting.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail="Meeting must be processed before evaluation"
        )
    
    # Create evaluator and dataset
    evaluator = RAGEvaluator()
    
    if use_sample:
        dataset = create_sample_dataset()
    else:
        # TODO: Load custom dataset
        dataset = create_sample_dataset()
    
    # Run evaluation
    try:
        results = evaluator.run_full_evaluation(meeting_id, dataset)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/metrics/{meeting_id}")
def get_metrics(
    meeting_id: int,
    metric_type: str = "all",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get specific metrics for a meeting
    
    metric_type: all, retrieval, generation, performance
    """
    # This would typically fetch from a stored evaluation
    # For now, return placeholder
    return {
        "meeting_id": meeting_id,
        "metric_type": metric_type,
        "message": "Run /run/{meeting_id} first to generate metrics"
    }


@router.post("/dataset/upload")
def upload_evaluation_dataset(
    dataset: Dict[str, Any],
    user_id: int = Depends(get_current_user_id)
):
    """
    Upload custom evaluation dataset
    
    Dataset format:
    {
        "questions": ["...", "..."],
        "ground_truth_answers": ["...", "..."],
        "relevant_chunks": [["..."], ["..."]],
        "metadata": [{}, {}]
    }
    """
    try:
        eval_dataset = EvaluationDataset()
        eval_dataset.questions = dataset.get("questions", [])
        eval_dataset.ground_truth_answers = dataset.get("ground_truth_answers", [])
        eval_dataset.relevant_chunks = dataset.get("relevant_chunks", [])
        eval_dataset.metadata = dataset.get("metadata", [])
        
        # Save to file
        dataset_path = Path("data/evaluation_datasets") / f"user_{user_id}_dataset.json"
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        eval_dataset.save(dataset_path)
        
        return {
            "status": "success",
            "samples": len(eval_dataset.questions),
            "path": str(dataset_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dataset format: {str(e)}"
        )


@router.get("/report/{meeting_id}")
def generate_report(
    meeting_id: int,
    format: str = "json",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Generate evaluation report
    
    format: json or markdown
    """
    # Verify access
    meeting_repo = MeetingRepository(db)
    meeting = meeting_repo.get_by_id(meeting_id)
    
    if not meeting or meeting.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    evaluator = RAGEvaluator()
    
    if format == "markdown":
        report = evaluator.generate_report()
        return {"format": "markdown", "report": report}
    else:
        # Return last results or run new evaluation
        if evaluator.results:
            return {"format": "json", "results": evaluator.results}
        else:
            return {
                "format": "json",
                "message": "No evaluation results. Run /run/{meeting_id} first."
            }


@router.get("/benchmark")
def get_benchmark_scores():
    """Get benchmark scores for comparison"""
    return {
        "retrieval": {
            "precision@5_target": 0.80,
            "recall@5_target": 0.70,
            "mrr_target": 0.85
        },
        "generation": {
            "faithfulness_target": 0.85,
            "relevance_target": 0.80,
            "hallucination_max": 0.15
        },
        "performance": {
            "max_latency_seconds": 2.0,
            "min_success_rate": 0.95
        }
    }
