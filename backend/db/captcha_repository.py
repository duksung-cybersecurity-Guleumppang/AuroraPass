from typing import List, Optional, Tuple
from sqlalchemy import text
from db.session import get_db_session
import random


class CaptchaRepository:
    
    def get_random_captcha(self) -> Optional[Tuple[str, str, str]]:
        """Get random CAPTCHA file: (id, filename, answer)"""
        with get_db_session() as session:
            result = session.execute(text("""
                SELECT id, filename, answer 
                FROM captcha_files 
                ORDER BY RANDOM() 
                LIMIT 1
            """)).fetchone()
            
            if result:
                return result.id, result.filename, result.answer
            return None
    
    def get_captcha_audio(self, captcha_id: str) -> Optional[Tuple[bytes, str]]:
        """Get CAPTCHA audio data: (audio_data, content_type)"""
        with get_db_session() as session:
            result = session.execute(text("""
                SELECT audio_data, content_type 
                FROM captcha_files 
                WHERE id = :captcha_id
            """), {"captcha_id": captcha_id}).fetchone()
            
            if result:
                return result.audio_data, result.content_type
            return None
    
    def get_captcha_answer(self, captcha_id: str) -> Optional[str]:
        """Get CAPTCHA answer by ID"""
        with get_db_session() as session:
            result = session.execute(text("""
                SELECT answer 
                FROM captcha_files 
                WHERE id = :captcha_id
            """), {"captcha_id": captcha_id}).fetchone()
            
            return result.answer if result else None


captcha_repository = CaptchaRepository()
