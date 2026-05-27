from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ExtractedAnswer:
    passage: str
    start: int
    end: int


class _QAPipeline:
    """
    Manual extractive QA pipeline compatible with transformers 5.x, which dropped
    the built-in ``question-answering`` pipeline task.
    """

    def __init__(self, model: Any, tokenizer: Any, torch: Any) -> None:
        self._model = model
        self._tokenizer = tokenizer
        self._torch = torch

    def __call__(self, question: str, context: str) -> dict:
        """
        Runs the QA model on the given question and context.
        
        Args:
            question: The question to answer.
            context: The context passage to search for the answer.
        Returns:
            A dictionary containing the answer and its score, or an empty answer if no valid answer 
            is found.
        """
        
        torch = self._torch
        inputs = self._tokenizer(
            question,
            context,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        seq_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = self._model(**inputs)

        start_probs = torch.softmax(outputs.start_logits[0], dim=0)
        end_probs = torch.softmax(outputs.end_logits[0], dim=0)

        # Vectorised best-valid-span: maximise P(start) * P(end) where start <= end
        # and the span is at most 100 tokens long.
        rows = torch.arange(seq_len).unsqueeze(1)
        cols = torch.arange(seq_len).unsqueeze(0)
        valid_mask = (cols >= rows) & ((cols - rows) < 100)
        score_matrix = torch.outer(start_probs, end_probs) * valid_mask.float()

        best_idx = int(score_matrix.argmax())
        best_start = best_idx // seq_len
        best_end = best_idx % seq_len
        score = float(score_matrix[best_start, best_end])

        answer_ids = inputs["input_ids"][0][best_start : best_end + 1]
        answer = self._tokenizer.decode(answer_ids, skip_special_tokens=True).strip()

        return {"score": score, "answer": answer}


class ExtractiveQA:
    """
    Lightweight wrapper around a HuggingFace extractive QA pipeline.
    """

    def __init__(self, model_name: str, min_score: float = 0.0) -> None:
        self._model_name = model_name
        self._min_score = min_score
        self._pipeline: Any = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _ensure_pipeline(self) -> Any:
        """
        Lazily initializes the QA pipeline on first use. This avoids the overhead of loading 
        the model at application startup, while still allowing for warming up the model if desired.
        """
        
        if self._pipeline is None:
            try:
                from transformers import (  # type: ignore[import]
                    AutoModelForQuestionAnswering,
                    AutoTokenizer,
                )
                import torch  # type: ignore[import]
            except Exception as exc:  # pragma: no cover - import error path
                raise RuntimeError(
                    "transformers is not installed. Install it with: pip install transformers"
                ) from exc

            tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            model = AutoModelForQuestionAnswering.from_pretrained(self._model_name)
            self._pipeline = _QAPipeline(model=model, tokenizer=tokenizer, torch=torch)
        return self._pipeline

    def warmup(self) -> None:
        """
        Warms up the QA model by running a dummy inference. This can help reduce latency for 
        the first real request.
        """
        
        qa_pipeline = self._ensure_pipeline()
        qa_pipeline(question="warmup", context="warmup context")

    def extract(self, question: str, context: str) -> Optional[ExtractedAnswer]:
        """
        Extracts an answer from the context for the given question using the QA model.
        
        Args:
            question: The question to answer.
            context: The context passage to search for the answer.
        Returns:
            An ExtractedAnswer containing the answer passage and its position in the context, or
            None if no valid answer is found.
        """
        
        question = question.strip()

        if not question or not context.strip():
            return None

        qa_pipeline = self._ensure_pipeline()
        output = qa_pipeline(question=question, context=context)

        if isinstance(output, list):
            if not output:
                return None
            output = output[0]

        if not isinstance(output, dict):
            return None

        score = float(output.get("score", 0.0))
        if score < self._min_score:
            return None

        answer = str(output.get("answer", "")).strip()

        # Some QA models return placeholders for "no answer".
        if not answer or answer.lower() in {"[cls]", "<s>", "</s>"}:
            return None

        start = output.get("start")
        end = output.get("end")
        if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(context):
            left = start
            right = end
            while left < right and context[left].isspace():
                left += 1
            while right > left and context[right - 1].isspace():
                right -= 1
            if left < right:
                return ExtractedAnswer(
                    passage=context[left:right],
                    start=left,
                    end=right,
                )

        found = context.find(answer)
        if found != -1:
            return ExtractedAnswer(
                passage=answer,
                start=found,
                end=found + len(answer),
            )

        return None

    def extract_many(self, question: str, contexts: list[str]) -> list[Optional[ExtractedAnswer]]:
        """
        Extracts answers from multiple contexts for the given question, returning a list of results
        corresponding to each context.
        
        Args:
            question: The question to answer.
            contexts: A list of context passages to search for the answer.
        Returns:
            A list of ExtractedAnswer objects or None values, one for each context, indicating the 
            answer found in that context (or None if no valid answer was found).
        """
        
        return [self.extract(question, context) for context in contexts]
