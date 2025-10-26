"""
Unit tests for the translator application.
Test các core functionality: token counting, patch splitting, validation.
"""
import pytest
import json
from pathlib import Path
from utils import (
    count_tokens,
    count_tokens_in_dict,
    split_into_patches,
    merge_patches,
    validate_translation,
    calculate_progress
)


class TestTokenCounting:
    """Test token counting functions."""
    
    def test_count_tokens_english(self):
        """Test đếm token cho English text."""
        text = "Hello world, this is a test string"
        tokens = count_tokens(text)
        assert tokens > 0
        # Estimate: ~36 chars / 3 * 1.1 = ~13 tokens
        assert 10 < tokens < 20
    
    def test_count_tokens_vietnamese(self):
        """Test đếm token cho Vietnamese text."""
        text = "Xin chào thế giới, đây là chuỗi test"
        tokens = count_tokens(text)
        assert tokens > 0
        # Vietnamese có dấu nên estimate khác một chút
        assert 10 < tokens < 25
    
    def test_count_tokens_in_dict(self):
        """Test đếm token trong dictionary."""
        data = {
            "key1": "Hello world",
            "key2": "This is a test"
        }
        tokens = count_tokens_in_dict(data)
        assert tokens > 0
        # Phải tính cả JSON structure (keys, quotes, braces, etc.)
        assert tokens > 20


class TestPatchSplitting:
    """Test patch splitting functionality."""
    
    def test_split_into_patches_small(self):
        """Test split với data nhỏ."""
        data = {
            f"key_{i}": f"Value {i}" for i in range(10)
        }
        patches = split_into_patches(data, token_limit=10000)
        
        # Data nhỏ nên chỉ cần 1 patch
        assert len(patches) == 1
        assert len(patches[0]) == 10
    
    def test_split_into_patches_large(self):
        """Test split với data lớn."""
        # Tạo data lớn với ~1000 entries
        data = {
            f"key_{i}": f"This is a longer value for testing purposes, entry number {i}" * 10
            for i in range(1000)
        }
        
        # Token limit nhỏ để force split
        patches = split_into_patches(data, token_limit=50000)
        
        # Phải có nhiều hơn 1 patch
        assert len(patches) > 1
        
        # Tổng số entries phải bằng original
        total_entries = sum(len(patch) for patch in patches)
        assert total_entries == 1000
    
    def test_split_preserves_data(self):
        """Test split không làm mất data."""
        data = {
            f"key_{i}": f"Value {i}" for i in range(100)
        }
        
        patches = split_into_patches(data, token_limit=10000)
        merged = merge_patches(patches)
        
        # Data sau khi merge phải giống original
        assert merged == data


class TestMergingPatches:
    """Test merging patches."""
    
    def test_merge_patches_simple(self):
        """Test merge các patches đơn giản."""
        patches = [
            {"key1": "value1", "key2": "value2"},
            {"key3": "value3", "key4": "value4"},
            {"key5": "value5"}
        ]
        
        merged = merge_patches(patches)
        
        assert len(merged) == 5
        assert merged["key1"] == "value1"
        assert merged["key5"] == "value5"
    
    def test_merge_patches_empty(self):
        """Test merge với patches rỗng."""
        patches = []
        merged = merge_patches(patches)
        assert merged == {}


class TestValidation:
    """Test validation functionality."""
    
    def test_validate_translation_success(self):
        """Test validation khi translation đầy đủ."""
        original = {
            "key1": "Hello",
            "key2": "World"
        }
        translated = {
            "key1": "Xin chào",
            "key2": "Thế giới"
        }
        
        is_valid, missing = validate_translation(original, translated)
        
        assert is_valid is True
        assert missing == []
    
    def test_validate_translation_missing_keys(self):
        """Test validation khi thiếu keys."""
        original = {
            "key1": "Hello",
            "key2": "World",
            "key3": "Test"
        }
        translated = {
            "key1": "Xin chào",
            "key2": "Thế giới"
        }
        
        is_valid, missing = validate_translation(original, translated)
        
        assert is_valid is False
        assert "key3" in missing
        assert len(missing) == 1
    
    def test_validate_translation_extra_keys_ok(self):
        """Test validation với extra keys (vẫn valid)."""
        original = {
            "key1": "Hello"
        }
        translated = {
            "key1": "Xin chào",
            "key2": "Extra"
        }
        
        is_valid, missing = validate_translation(original, translated)
        
        # Extra keys không ảnh hưởng validation
        assert is_valid is True
        assert missing == []


class TestProgressCalculation:
    """Test progress calculation."""
    
    def test_calculate_progress_zero(self):
        """Test progress khi chưa bắt đầu."""
        progress = calculate_progress(0, 10)
        assert progress == 0.0
    
    def test_calculate_progress_half(self):
        """Test progress ở giữa chừng."""
        progress = calculate_progress(5, 10)
        assert progress == 50.0
    
    def test_calculate_progress_complete(self):
        """Test progress khi hoàn thành."""
        progress = calculate_progress(10, 10)
        assert progress == 100.0
    
    def test_calculate_progress_zero_total(self):
        """Test progress với total = 0."""
        progress = calculate_progress(0, 0)
        assert progress == 100.0


class TestIntegration:
    """Integration tests với example data."""
    
    def test_example_file_processing(self):
        """Test xử lý example file."""
        example_file = Path("example/NMS_LOC_4_ENGLISH.json")
        
        if not example_file.exists():
            pytest.skip("Example file not found")
        
        # Load example data
        with open(example_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Count tokens
        tokens = count_tokens_in_dict(data)
        assert tokens > 0
        
        # Split into patches
        patches = split_into_patches(data, token_limit=100000)
        assert len(patches) > 0
        
        # Verify split preserves data
        merged = merge_patches(patches)
        assert len(merged) == len(data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
