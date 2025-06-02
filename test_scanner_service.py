import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from scanner_service import ScannerService
from models import FileScan

@pytest.fixture
def scanner_service():
    return ScannerService()

@pytest.fixture
def mock_db():
    return Mock()

def test_get_file_hash():
    service = ScannerService()
    test_bytes = b"test content"
    hash_result = service.get_file_hash(test_bytes)
    assert isinstance(hash_result, str)
    assert len(hash_result) == 64  # SHA-256 produces 64 character hex string

def test_scan_for_virus_clean_file():
    service = ScannerService()
    clean_content = b"This is a clean file"
    assert not service.scan_for_virus(clean_content)

def test_scan_for_virus_infected_file():
    service = ScannerService()
    virus_content = b"This file contains a virus"
    assert service.scan_for_virus(virus_content)

def test_scan_file_empty(scanner_service, mock_db):
    with pytest.raises(ValueError, match="Empty file uploaded"):
        scanner_service.scan_file(mock_db, b"", "empty.txt")

def test_scan_file_cached(scanner_service, mock_db):
    # Setup mock cached scan
    cached_scan = FileScan(
        file_hash="test_hash",
        scan_result=True,
        filename="test.txt",
        scan_timestamp=datetime.now()
    )
    mock_db.query.return_value.filter.return_value.first.return_value = cached_scan

    result, is_cached = scanner_service.scan_file(mock_db, b"test content", "test.txt")
    
    assert is_cached
    assert "already been scanned" in result
    assert "Virus detected" in result
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()

def test_scan_file_new(scanner_service, mock_db):
    # Setup mock for no cache hit
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    result, is_cached = scanner_service.scan_file(mock_db, b"clean content", "test.txt")
    
    assert not is_cached
    assert "File is clean" in result
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

def test_get_stats(scanner_service, mock_db):
    # Setup mock query results
    mock_query = Mock()
    mock_filtered = Mock()
    
    # Setup the chain of mock calls
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filtered
    
    # Set return values for the count calls
    mock_query.count.return_value = 10  # total files
    mock_filtered.count.return_value = 3  # virus count
    
    stats = scanner_service.get_stats(mock_db)
    
    assert stats["total_files_scanned"] == 10
    assert stats["total_viruses_detected"] == 3
    assert stats["cache_size"] == 10
    
    # Verify the mock calls
    mock_db.query.assert_called()
    mock_query.filter.assert_called_once() 