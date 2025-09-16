from typing import List, Optional, Tuple
from sqlalchemy import text
from db.session import get_db_session
import random


class CaptchaRepository:
    
    def get_random_captcha(self) -> Optional[Tuple[str, str, str, bytes, str]]:
        """Get and atomically consume available CAPTCHA: (id, filename, answer, audio_data, content_type)"""
        with get_db_session() as session:
            result = session.execute(text("""
                WITH picked AS (
                  SELECT id
                  FROM captcha_files
                  WHERE used = false AND (expires_at IS NULL OR expires_at > now())
                  ORDER BY random()
                  FOR UPDATE SKIP LOCKED
                  LIMIT 1
                )
                UPDATE captcha_files c
                SET used = true
                FROM picked p
                WHERE c.id = p.id
                RETURNING c.id, c.filename, c.answer, c.audio_data, c.content_type
            """)).fetchone()
            
            if result:
                session.commit()
                return result.id, result.filename, result.answer, result.audio_data, result.content_type
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
