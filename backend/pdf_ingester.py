import os
import glob
import logging
import fitz  # PyMuPDF
import google.generativeai as genai
from langchain_text_splitters import MarkdownTextSplitter
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("pagani.pdf_ingester")

# Configure Gemini for Vision
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use gemini-1.5-flash for fast vision processing
VISION_MODEL = "gemini-1.5-flash"

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "pagani_intelligence_rich_dataset_25_pdfs")

def summarize_image(image_bytes: bytes) -> str:
    """Pass image bytes to Gemini Vision to generate a description."""
    try:
        model = genai.GenerativeModel(VISION_MODEL)
        prompt = "Describe this technical diagram, chart, or image from a Pagani hypercar manual in detail. Focus on engineering specs and parts."
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        return response.text if response.text else ""
    except Exception as e:
        logger.warning(f"Image summarization failed: {e}")
        return ""

def ingest_all_pdfs() -> list[dict]:
    """
    Load all PDFs, extract text and images, summarize images,
    and semantic chunk using Markdown Splitter.
    """
    if not os.path.exists(PDF_DIR):
        logger.error(f"PDF directory not found: {PDF_DIR}")
        return []

    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {PDF_DIR}")
        return []

    logger.info(f"Advanced PDF Ingestion: Found {len(pdf_files)} PDFs.")
    
    # Semantic chunking along markdown headers rather than pure character math
    text_splitter = MarkdownTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    all_chunks = []
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        logger.info(f"Processing Multi-Modal PDF: {filename}")
        
        try:
            doc = fitz.open(pdf_path)
            full_markdown = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                # Build page markdown
                page_md = f"\n\n## Page {page_num + 1}\n\n{page_text}\n\n"
                
                # Extract images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    logger.info(f"Found image on page {page_num+1} of {filename}. Summarizing...")
                    img_summary = summarize_image(image_bytes)
                    if img_summary:
                        page_md += f"### Image {img_index+1} Description:\n{img_summary}\n\n"
                
                full_markdown += page_md
                
            # Split into chunks based on markdown structure
            chunks = text_splitter.create_documents([full_markdown])
            
            for i, chunk in enumerate(chunks):
                chunk_dict = {
                    "content": chunk.page_content,
                    "source": filename,
                    # We can't guarantee exact page number mapping after markdown splitting,
                    "page_number": 0,
                    "chunk_id": f"{filename}_chunk_{i}",
                    "role_access": ["admin", "engineer", "viewer"],
                    "is_pdf": True
                }
                all_chunks.append(chunk_dict)
                
            logger.info(f"Multi-Modal PDF processed: {filename} ({len(chunks)} semantic chunks)")
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")

    logger.info(f"Multi-Modal PDF ingestion complete: {len(all_chunks)} total chunks created.")
    return all_chunks
