"""
PDF processing and text extraction
"""

import io
import logging
from typing import Optional
import PyPDF2
from pdfplumber import PDF
import asyncio

logger = logging.getLogger(__name__)


class PDFParser:
    """PDF text extraction with multiple fallback methods"""
    
    def __init__(self):
        self.extraction_methods = [
            self._extract_with_pdfplumber,
            self._extract_with_pypdf2,
            self._extract_with_basic_text
        ]
    
    async def extract_text(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF using multiple methods
        Returns the best extraction result
        """
        
        results = []
        
        for method in self.extraction_methods:
            try:
                text = await method(pdf_content)
                if text and len(text.strip()) > 0:
                    results.append({
                        'method': method.__name__,
                        'text': text,
                        'length': len(text.strip()),
                        'quality_score': self._calculate_quality_score(text)
                    })
            except Exception as e:
                logger.warning(f"PDF extraction method {method.__name__} failed: {e}")
                continue
        
        if not results:
            raise ValueError("Unable to extract text from PDF using any method")
        
        # Return the result with the highest quality score
        best_result = max(results, key=lambda x: x['quality_score'])
        logger.info(f"PDF extraction successful using {best_result['method']} "
                   f"(quality: {best_result['quality_score']:.2f})")
        
        return best_result['text']
    
    async def _extract_with_pdfplumber(self, pdf_content: bytes) -> str:
        """Extract text using pdfplumber (most accurate for complex layouts)"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._pdfplumber_extraction,
                pdf_content
            )
        except ImportError:
            raise ValueError("pdfplumber not available")
    
    def _pdfplumber_extraction(self, pdf_content: bytes) -> str:
        """Synchronous pdfplumber extraction"""
        import pdfplumber
        
        text_parts = []
        
        with io.BytesIO(pdf_content) as pdf_buffer:
            with pdfplumber.open(pdf_buffer) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"--- Page {page_num + 1} ---\n")
                            text_parts.append(page_text)
                            text_parts.append("\n\n")
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        continue
        
        return ''.join(text_parts)
    
    async def _extract_with_pypdf2(self, pdf_content: bytes) -> str:
        """Extract text using PyPDF2 (fallback method)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._pypdf2_extraction,
            pdf_content
        )
    
    def _pypdf2_extraction(self, pdf_content: bytes) -> str:
        """Synchronous PyPDF2 extraction"""
        text_parts = []
        
        with io.BytesIO(pdf_content) as pdf_buffer:
            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n")
                        text_parts.append(page_text)
                        text_parts.append("\n\n")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    continue
        
        return ''.join(text_parts)
    
    async def _extract_with_basic_text(self, pdf_content: bytes) -> str:
        """Basic text extraction as last resort"""
        # This is a very basic fallback - just try to decode as text
        try:
            return pdf_content.decode('utf-8', errors='ignore')
        except Exception:
            return pdf_content.decode('latin-1', errors='ignore')
    
    def _calculate_quality_score(self, text: str) -> float:
        """
        Calculate quality score for extracted text
        Higher score = better extraction
        """
        if not text or len(text.strip()) == 0:
            return 0.0
        
        score = 0.0
        
        # Length bonus (longer text usually better)
        score += min(len(text) / 1000.0, 10.0)
        
        # Medical terminology bonus
        medical_terms = [
            'patient', 'medication', 'doctor', 'hospital', 'diagnosis',
            'treatment', 'discharge', 'follow-up', 'appointment', 'dosage',
            'symptoms', 'condition', 'therapy', 'prescription', 'clinical'
        ]
        
        text_lower = text.lower()
        medical_score = sum(1 for term in medical_terms if term in text_lower)
        score += medical_score * 0.5
        
        # Structure bonus (proper sentences and paragraphs)
        sentences = text.count('.')
        paragraphs = text.count('\n\n')
        score += (sentences / 100.0) + (paragraphs / 10.0)
        
        # Penalty for too many special characters (indicates poor extraction)
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' .,!?\n\t-')
        special_ratio = special_chars / max(len(text), 1)
        if special_ratio > 0.3:
            score *= 0.5
        
        return score


class PDFMetadataExtractor:
    """Extract metadata from PDF documents"""
    
    @staticmethod
    async def extract_metadata(pdf_content: bytes) -> dict:
        """Extract PDF metadata"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            PDFMetadataExtractor._extract_metadata_sync,
            pdf_content
        )
    
    @staticmethod
    def _extract_metadata_sync(pdf_content: bytes) -> dict:
        """Synchronous metadata extraction"""
        metadata = {}
        
        try:
            with io.BytesIO(pdf_content) as pdf_buffer:
                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                
                # Basic info
                metadata['page_count'] = len(pdf_reader.pages)
                
                # Document info
                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    metadata['title'] = info.get('/Title', '')
                    metadata['author'] = info.get('/Author', '')
                    metadata['subject'] = info.get('/Subject', '')
                    metadata['creator'] = info.get('/Creator', '')
                    metadata['producer'] = info.get('/Producer', '')
                    metadata['creation_date'] = str(info.get('/CreationDate', ''))
                    metadata['modification_date'] = str(info.get('/ModDate', ''))
                
                # Security info
                metadata['encrypted'] = pdf_reader.is_encrypted
                
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            metadata['error'] = str(e)
        
        return metadata
