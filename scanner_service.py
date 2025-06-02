import hashlib
from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from models import FileScan

class ScannerService:
    @staticmethod
    def get_file_hash(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def scan_for_virus(file_bytes: bytes) -> bool:
        try:
            text = file_bytes.decode(errors="ignore")
            return "virus" in text.lower()
        except Exception:
            return False

    @staticmethod
    def check_cached_scan(db: Session, file_hash: str) -> Optional[FileScan]:
        return db.query(FileScan).filter(FileScan.file_hash == file_hash).first()

    def scan_file(self, db: Session, file_bytes: bytes, filename: str) -> Tuple[str, bool]:
        """
        Scans a file for viruses and manages the scan results in the database.
        
        Args:
            db: Database session
            file_bytes: The contents of the file to scan
            filename: Name of the file being scanned
            
        Returns:
            Tuple[str, bool]: (result message, is_cached)
        """
        if not file_bytes:
            raise ValueError("Empty file uploaded.")

        file_hash = self.get_file_hash(file_bytes)
        cached_scan = self.check_cached_scan(db, file_hash)

        if cached_scan:
            result = f"File has already been scanned. {'Virus detected!!' if cached_scan.scan_result else 'File is clean!!'}"
            return result, True

        is_virus = self.scan_for_virus(file_bytes)
        new_scan = FileScan(
            file_hash=file_hash,
            scan_result=is_virus,
            filename=filename,
            scan_timestamp=datetime.now()
        )
        db.add(new_scan)
        db.commit()

        result = "Virus detected" if is_virus else "File is clean"
        return result, False

    @staticmethod
    def get_stats(db: Session) -> dict:
        """Get scanning statistics from the database."""
        total = db.query(FileScan).count()
        viruses = db.query(FileScan).filter(FileScan.scan_result == True).count()
        return {
            "total_files_scanned": total,
            "total_viruses_detected": viruses,
            "cache_size": total
        } 