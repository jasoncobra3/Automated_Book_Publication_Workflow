import os
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging
import os
from dotenv import load_dotenv
load_dotenv()

groq_api_key=os.environ["GROQ_API_KEY"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ChapterProcessor:
    def __init__(self, groq_api_key: str, model_name: str = "Llama3-70b-8192"):
        """
        Initializes the processor with Groq's LLM and sets up the LangChain pipeline.
        """
        self.llm = ChatGroq(
            temperature=0.7,  # Controls creativity
            groq_api_key=groq_api_key,
            model_name=model_name
        )
        self.chain = self._build_chain()
        
    def _build_chain(self):
        """LangChain pipeline for consistent rewriting"""
        prompt = ChatPromptTemplate.from_template(
            """Rewrite this book chapter creatively while preserving:
            - Key plot points
            - Character personalities
            - Original tone
            
            Return ONLY the rewritten text, no additional commentary.
            
            Original Chapter:
            {input_text}
            """
        )
        return prompt | self.llm | StrOutputParser()

    def rewrite_chapter(self, text: str) -> str:
        """Process text through Groq's LLM"""
        try:
            logger.info("Spinning chapter text...")
            return self.chain.invoke({"input_text": text})
        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}")
            raise

    def process_chapter(self, input_path: str):
        """End-to-end file processing"""
        try:
            # Read input
            with open(input_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Process text
            rewritten_text = self.rewrite_chapter(text)
            
            # Save output
            output_dir = Path("data/processed")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"Spinned_{Path(input_path).name}"
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rewritten_text)
            
            logger.info(f"Saved processed chapter to: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to process {input_path}: {str(e)}")
            return None

if __name__ == "__main__":
    
    processor = ChapterProcessor(groq_api_key=groq_api_key)
    sample_chapter = "data/raw/Chapter_1.txt"
    processor.process_chapter(sample_chapter)