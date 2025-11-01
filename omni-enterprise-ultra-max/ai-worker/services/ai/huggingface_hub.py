"""
HuggingFace Model Hub Integration
Access 100,000+ pre-trained models and datasets
"""

import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# HuggingFace Hub token
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
HF_ENABLED = bool(HF_TOKEN)

if HF_ENABLED:
    try:
        from transformers import (
            AutoTokenizer,
            AutoModel,
            AutoModelForSequenceClassification,
            AutoModelForCausalLM,
            pipeline,
            Trainer,
            TrainingArguments
        )
        from datasets import load_dataset
        from huggingface_hub import (
            HfApi,
            hf_hub_download,
            list_models,
            login
        )
        
        # Login to HuggingFace Hub
        if HF_TOKEN:
            login(token=HF_TOKEN)
            logger.info("✅ Logged into HuggingFace Hub")
        
        class HuggingFaceService:
            """
            HuggingFace Hub integration for model downloading,
            fine-tuning, and dataset access
            """
            
            def __init__(self):
                self.api = HfApi()
                self.loaded_models = {}
                self.loaded_pipelines = {}
            
            async def search_models(
                self,
                task: Optional[str] = None,
                query: Optional[str] = None,
                limit: int = 10
            ) -> List[Dict[str, Any]]:
                """
                Search HuggingFace Hub for models
                
                Args:
                    task: Task type (text-classification, text-generation, etc.)
                    query: Search query
                    limit: Max results
                
                Returns:
                    List of model metadata
                """
                try:
                    models = list_models(
                        filter=task,
                        search=query,
                        limit=limit,
                        sort="downloads",
                        direction=-1
                    )
                    
                    results = []
                    for model in models:
                        results.append({
                            "model_id": model.modelId,
                            "downloads": getattr(model, 'downloads', 0),
                            "likes": getattr(model, 'likes', 0),
                            "tags": model.tags,
                            "pipeline_tag": getattr(model, 'pipeline_tag', None)
                        })
                    
                    return results
                
                except Exception as e:
                    logger.error(f"Model search failed: {e}")
                    return []
            
            async def load_model(
                self,
                model_id: str,
                task: str = "text-classification"
            ) -> Optional[Any]:
                """
                Load pre-trained model from Hub
                
                Args:
                    model_id: HuggingFace model ID (e.g., "bert-base-uncased")
                    task: Task type
                
                Returns:
                    Loaded model pipeline
                """
                try:
                    if model_id in self.loaded_pipelines:
                        return self.loaded_pipelines[model_id]
                    
                    logger.info(f"📥 Downloading model: {model_id}")
                    
                    # Create pipeline
                    pipe = pipeline(task, model=model_id, token=HF_TOKEN)
                    self.loaded_pipelines[model_id] = pipe
                    
                    logger.info(f"✅ Model loaded: {model_id}")
                    return pipe
                
                except Exception as e:
                    logger.error(f"Model loading failed for {model_id}: {e}")
                    return None
            
            async def run_inference(
                self,
                model_id: str,
                input_text: str,
                task: str = "text-classification"
            ) -> Dict[str, Any]:
                """
                Run inference on text using HuggingFace model
                
                Args:
                    model_id: Model ID
                    input_text: Input text
                    task: Task type
                
                Returns:
                    Inference results
                """
                try:
                    pipe = await self.load_model(model_id, task)
                    if not pipe:
                        return {"error": "Model loading failed"}
                    
                    result = pipe(input_text)
                    
                    return {
                        "model": model_id,
                        "task": task,
                        "input": input_text,
                        "output": result
                    }
                
                except Exception as e:
                    logger.error(f"Inference failed: {e}")
                    return {"error": str(e)}
            
            async def load_dataset(
                self,
                dataset_name: str,
                split: str = "train",
                streaming: bool = False
            ) -> Optional[Any]:
                """
                Load dataset from HuggingFace Datasets
                
                Args:
                    dataset_name: Dataset ID (e.g., "imdb", "squad")
                    split: Dataset split (train, test, validation)
                    streaming: Stream large datasets
                
                Returns:
                    Dataset object
                """
                try:
                    logger.info(f"📥 Loading dataset: {dataset_name}")
                    
                    dataset = load_dataset(
                        dataset_name,
                        split=split,
                        streaming=streaming
                    )
                    
                    logger.info(f"✅ Dataset loaded: {dataset_name}")
                    return dataset
                
                except Exception as e:
                    logger.error(f"Dataset loading failed: {e}")
                    return None
            
            async def fine_tune_model(
                self,
                base_model: str,
                train_dataset: Any,
                eval_dataset: Any,
                output_dir: str = "./fine_tuned_model",
                epochs: int = 3,
                batch_size: int = 8
            ) -> Dict[str, Any]:
                """
                Fine-tune a HuggingFace model on custom data
                
                Args:
                    base_model: Base model ID
                    train_dataset: Training dataset
                    eval_dataset: Evaluation dataset
                    output_dir: Output directory
                    epochs: Training epochs
                    batch_size: Batch size
                
                Returns:
                    Training results
                """
                try:
                    logger.info(f"🔧 Fine-tuning {base_model}")
                    
                    # Load model and tokenizer
                    model = AutoModelForSequenceClassification.from_pretrained(base_model)
                    tokenizer = AutoTokenizer.from_pretrained(base_model)
                    
                    # Training arguments
                    training_args = TrainingArguments(
                        output_dir=output_dir,
                        num_train_epochs=epochs,
                        per_device_train_batch_size=batch_size,
                        per_device_eval_batch_size=batch_size,
                        warmup_steps=500,
                        weight_decay=0.01,
                        logging_dir='./logs',
                        logging_steps=10,
                        evaluation_strategy="epoch",
                        save_strategy="epoch",
                        load_best_model_at_end=True
                    )
                    
                    # Trainer
                    trainer = Trainer(
                        model=model,
                        args=training_args,
                        train_dataset=train_dataset,
                        eval_dataset=eval_dataset,
                        tokenizer=tokenizer
                    )
                    
                    # Train
                    train_result = trainer.train()
                    
                    # Save model
                    trainer.save_model(output_dir)
                    
                    return {
                        "status": "success",
                        "output_dir": output_dir,
                        "train_loss": train_result.training_loss,
                        "epochs": epochs
                    }
                
                except Exception as e:
                    logger.error(f"Fine-tuning failed: {e}")
                    return {"status": "error", "message": str(e)}
            
            async def generate_text(
                self,
                prompt: str,
                model_id: str = "gpt2",
                max_length: int = 100,
                temperature: float = 0.7
            ) -> Dict[str, Any]:
                """
                Generate text using causal LM
                
                Args:
                    prompt: Input prompt
                    model_id: Model ID
                    max_length: Max tokens
                    temperature: Sampling temperature
                
                Returns:
                    Generated text
                """
                try:
                    generator = await self.load_model(model_id, "text-generation")
                    if not generator:
                        return {"error": "Model loading failed"}
                    
                    result = generator(
                        prompt,
                        max_length=max_length,
                        temperature=temperature,
                        num_return_sequences=1
                    )
                    
                    return {
                        "prompt": prompt,
                        "generated_text": result[0]['generated_text'],
                        "model": model_id
                    }
                
                except Exception as e:
                    logger.error(f"Text generation failed: {e}")
                    return {"error": str(e)}
            
            async def summarize_text(
                self,
                text: str,
                model_id: str = "facebook/bart-large-cnn",
                max_length: int = 130,
                min_length: int = 30
            ) -> Dict[str, Any]:
                """
                Summarize long text
                
                Args:
                    text: Input text
                    model_id: Summarization model
                    max_length: Max summary length
                    min_length: Min summary length
                
                Returns:
                    Summary
                """
                try:
                    summarizer = await self.load_model(model_id, "summarization")
                    if not summarizer:
                        return {"error": "Model loading failed"}
                    
                    result = summarizer(
                        text,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False
                    )
                    
                    return {
                        "original_text": text,
                        "summary": result[0]['summary_text'],
                        "model": model_id
                    }
                
                except Exception as e:
                    logger.error(f"Summarization failed: {e}")
                    return {"error": str(e)}
            
            async def translate_text(
                self,
                text: str,
                source_lang: str = "en",
                target_lang: str = "de",
                model_id: str = "Helsinki-NLP/opus-mt-en-de"
            ) -> Dict[str, Any]:
                """
                Translate text between languages
                
                Args:
                    text: Input text
                    source_lang: Source language code
                    target_lang: Target language code
                    model_id: Translation model
                
                Returns:
                    Translated text
                """
                try:
                    translator = await self.load_model(model_id, "translation")
                    if not translator:
                        return {"error": "Model loading failed"}
                    
                    result = translator(text)
                    
                    return {
                        "original": text,
                        "translated": result[0]['translation_text'],
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "model": model_id
                    }
                
                except Exception as e:
                    logger.error(f"Translation failed: {e}")
                    return {"error": str(e)}
        
        # Singleton instance
        _hf_service = HuggingFaceService()
        
        def get_huggingface_service() -> HuggingFaceService:
            return _hf_service
    
    except ImportError as e:
        logger.warning(f"HuggingFace libraries not fully available: {e}")
        HF_ENABLED = False

if not HF_ENABLED:
    # Dummy service when HuggingFace is disabled
    class HuggingFaceService:
        async def search_models(self, task=None, query=None, limit=10):
            return []
        
        async def load_model(self, model_id: str, task: str = "text-classification"):
            return None
        
        async def run_inference(self, model_id: str, input_text: str, task: str = "text-classification"):
            return {"error": "HuggingFace not configured"}
        
        async def load_dataset(self, dataset_name: str, split: str = "train", streaming: bool = False):
            return None
        
        async def fine_tune_model(self, base_model: str, train_dataset, eval_dataset, **kwargs):
            return {"status": "error", "message": "HuggingFace not configured"}
        
        async def generate_text(self, prompt: str, **kwargs):
            return {"error": "HuggingFace not configured"}
        
        async def summarize_text(self, text: str, **kwargs):
            return {"error": "HuggingFace not configured"}
        
        async def translate_text(self, text: str, **kwargs):
            return {"error": "HuggingFace not configured"}
    
    def get_huggingface_service() -> HuggingFaceService:
        return HuggingFaceService()
