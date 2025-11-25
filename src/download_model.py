"""
One-time script to download and cache RoBERTa-large model for offline use.
Run this once with internet connection, then all subsequent work is offline.
"""

from transformers import RobertaTokenizer, RobertaModel
import os

def download_and_cache_model(model_name='roberta-large', save_dir='../models/roberta-large'):
    """
    Download RoBERTa model and tokenizer, save to local directory
    
    Args:
        model_name: HuggingFace model identifier
        save_dir: Local directory to save model files
    """
    print(f"Downloading {model_name}...")
    print("This is a one-time download. Future loads will be offline.")
    
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Download model and tokenizer
    print("Downloading tokenizer...")
    tokenizer = RobertaTokenizer.from_pretrained(model_name)
    
    print("Downloading model (this may take a few minutes)...")
    model = RobertaModel.from_pretrained(model_name)
    
    # Save locally
    print(f"Saving to {save_dir}...")
    tokenizer.save_pretrained(save_dir)
    model.save_pretrained(save_dir)
    
    print(f"\n✓ Model cached successfully!")
    print(f"Location: {os.path.abspath(save_dir)}")
    print(f"Size: ~1.4GB")
    print("\nYou can now work completely offline.")
    
    # Test loading from local
    print("\nTesting offline load...")
    test_tokenizer = RobertaTokenizer.from_pretrained(save_dir, local_files_only=True)
    test_model = RobertaModel.from_pretrained(save_dir, local_files_only=True)
    print("✓ Offline loading works!")

if __name__ == "__main__":
    download_and_cache_model()
