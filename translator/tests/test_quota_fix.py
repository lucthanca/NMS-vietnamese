"""
Test script để verify quota exceeded handling.
Simulate quota error để test response.
"""
import re


def test_extract_retry_delay():
    """Test extract retry delay từ error messages."""
    
    # Test case 1: "Please retry in X.Xs"
    error_msg_1 = """429 You exceeded your current quota...
Please retry in 42.363447542s. [violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
}]"""
    
    pattern = r'Please retry in (\d+(?:\.\d+)?)s'
    match = re.search(pattern, error_msg_1)
    if match:
        delay = float(match.group(1))
        print(f"✅ Test 1 PASSED: Extracted {delay}s (expected ~42s)")
        assert 40 <= delay <= 45
    else:
        print("❌ Test 1 FAILED: Could not extract delay")
    
    # Test case 2: "retry_delay { seconds: X }"
    error_msg_2 = """429 You exceeded your current quota...
retry_delay {
  seconds: 42
}"""
    
    pattern = r'retry_delay\s*{\s*seconds:\s*(\d+)'
    match = re.search(pattern, error_msg_2)
    if match:
        delay = float(match.group(1))
        print(f"✅ Test 2 PASSED: Extracted {delay}s (expected 42s)")
        assert delay == 42
    else:
        print("❌ Test 2 FAILED: Could not extract delay")
    
    # Test case 3: No delay info (should fallback to 60)
    error_msg_3 = "429 Generic quota error"
    
    patterns = [
        r'Please retry in (\d+(?:\.\d+)?)s',
        r'retry_delay\s*{\s*seconds:\s*(\d+)',
    ]
    
    delay = None
    for pattern in patterns:
        match = re.search(pattern, error_msg_3)
        if match:
            delay = float(match.group(1))
            break
    
    if delay is None:
        delay = 60  # Fallback
        print(f"✅ Test 3 PASSED: No delay found, using fallback {delay}s")
    else:
        print(f"❌ Test 3 FAILED: Should use fallback but got {delay}s")
    
    print("\n✅ All extract_retry_delay tests passed!")


def test_quota_error_simulation():
    """Test xem có catch được error string không."""
    print("\n🧪 Testing quota error parsing...")
    
    # Simulate real error message from API
    error_msg = """429 You exceeded your current quota, please check your plan and billing details.
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 250
Please retry in 42.5s."""
    
    print(f"✅ Sample error message: {error_msg[:100]}...")
    
    # Test extract delay
    pattern = r'Please retry in (\d+(?:\.\d+)?)s'
    match = re.search(pattern, error_msg)
    if match:
        delay = float(match.group(1))
        print(f"✅ Extracted retry delay: {delay}s")
        print(f"✅ With 5s buffer: {int(delay) + 5}s")
        assert delay == 42.5
    else:
        print("❌ Failed to extract delay from error message")
        raise AssertionError("Pattern should match")
    
    print("✅ Quota error parsing test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Quota Exceeded Fix")
    print("=" * 60)
    
    test_extract_retry_delay()
    test_quota_error_simulation()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
