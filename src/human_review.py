from pathlib import Path
from src.version_control import store_version
import logging
from src.rl_search import RLSearchEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def show_suggestions(current_text: str) -> list:
    """Get top 3 relevant passages from other chapters"""
    searcher = RLSearchEngine()
    return searcher.search(
        query=current_text[:150], # Use first 150 chars for context
        top_k=3
    )

def get_latest_spinned_file() -> Path:
    """Finds the most recent AI-processed file"""
    processed_dir = Path("data/processed")
    spinned_files = list(processed_dir.glob("Spinned_*.txt"))
    
    if not spinned_files:
        raise FileNotFoundError("No spinned files found. Run ai_processor.py first.")
    
    return max(spinned_files, key=lambda f: f.stat().st_ctime)

def review_chapter():
    """CLI for human review of AI-spun chapters"""
    try:
        spinned_file = get_latest_spinned_file()
        with open(spinned_file, "r", encoding="utf-8") as f:
            ai_text = f.read()
        
        print(f"\n=== Reviewing: {spinned_file.name} ===")
        print(ai_text[:500] + "...\n")  # First 500 characters
        
        # Get human input 
        if input("Show writing suggestions? (y/n): ").lower() == 'y':
            suggestions = show_suggestions(ai_text)
            print("\n=== Recommended Edits ===")
            for i, (vid, score, text) in enumerate(suggestions):
                print(f"{i+1}. [Score: {score:.2f}]\n{text}\n")
            
            choice = input("Apply suggestion? (1-3 or 0 to skip): ")
            if choice.isdigit() and 1 <= int(choice) <= 3:
                final_text = suggestions[int(choice)-1][2]
            else:
                final_text = input("Paste your edited text (or press Enter to approve as-is): ") or ai_text
        else:
            final_text = input("Paste your edited text (or press Enter to approve as-is): ") or ai_text
        
        # Save human version
        human_file = spinned_file.parent / f"HumanEdited_{spinned_file.name}"
        with open(human_file, "w", encoding="utf-8") as f:
            f.write(final_text)
        
        #  Store in version control
        store_version(
            text=final_text,
            source_file=spinned_file.name,
            version_type="human_approved" if final_text == ai_text else "human_edited"
        )
        logger.info(f"Human review saved to: {human_file}")
        
    except Exception as e:
        logger.error(f"Review failed: {str(e)}")
        raise

if __name__ == "__main__":
    review_chapter()