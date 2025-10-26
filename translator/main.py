#!/usr/bin/env python3
"""
AI Agent Vietnamese Translator for No Man's Sky
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict

from state import TranslationState
from workflows.sequence_wf import create_sequence_workflow
from workflows.parallel_wf import create_parallel_workflow
from progress import print_header, print_error, print_success, TranslationProgress


def run_workflow(wf_type: str, loc_filename: str, token_limit: int = 50000, max_retries: int = 3) -> Dict:
    """
    Run the translation workflow.
    
    Args:
        wf_type: Workflow type (sequence/full_parallel)
        loc_filename: Localization filename
        token_limit: Token limit cho mỗi patch (default: 50000 - safe for Gemini output limit 65,535)
        max_retries: Số lần retry tối đa
        
    Returns:
        Dict với success status và thông tin khác
    """
    start_time = datetime.now()
    
    try:
        # Tạo workflow dựa vào type
        if wf_type == "sequence":
            workflow = create_sequence_workflow()
        elif wf_type == "full_parallel":
            workflow = create_parallel_workflow()
        else:
            return {
                "success": False,
                "error": f"Unknown workflow type: {wf_type}"
            }
        
        # Tạo initial state
        initial_state: TranslationState = {
            "loc_name": loc_filename,
            "token_limit": token_limit,
            "original_data": None,
            "patches": [],
            "current_patch_index": 0,
            "translated_patches": [],
            "failed_patches": [],
            "retry_count": 0,
            "max_retries": max_retries,
            "errors": [],
            "completed": False,
            "progress": 0.0
        }
        
        # Chạy workflow
        print(f"\n🔄 Starting {wf_type} workflow...")
        print(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Invoke workflow
        final_state = workflow.invoke(initial_state)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Kiểm tra kết quả
        if final_state.get('completed') and not final_state.get('errors'):
            print(f"\n⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Total execution time: {execution_time:.2f}s")
            
            # In summary
            stats = {
                'total_entries': len(final_state.get('original_data', {})),
                'total_patches': len(final_state.get('patches', [])),
                'successful_patches': len(final_state.get('translated_patches', [])),
                'failed_patches': len(final_state.get('failed_patches', [])),
                'execution_time': execution_time
            }
            
            progress_tracker = TranslationProgress(stats['total_patches'])
            progress_tracker.print_summary(stats)
            
            return {
                "success": True,
                "execution_time": execution_time,
                "stats": stats
            }
        else:
            errors = final_state.get('errors', [])
            error_msg = "; ".join(errors) if errors else "Unknown error"
            
            print(f"\n⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Total execution time: {execution_time:.2f}s")
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }
            
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"\n⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total execution time: {execution_time:.2f}s")
        
        return {
            "success": False,
            "error": str(e),
            "execution_time": execution_time
        }


def main():
    """Main entry point for the translator application."""
    parser = argparse.ArgumentParser(
        description="AI Agent Vietnamese Translator for No Man's Sky",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                      # Run sequence workflow
  python main.py --wf-type full_parallel              # Run full parallel workflow
  python main.py -wt sequence -l NMS_LOC1_ENGLISH.JSON  # Custom file
  python main.py --token-limit 50000                  # Custom token limit
        """
    )
    
    parser.add_argument(
        "--wf-type", "-wt",
        default="sequence",
        choices=["sequence", "full_parallel"],
        help="Workflow type to execute (default: sequence)"
    )
    
    parser.add_argument(
        "--loc-filename", "-l",
        default="NMS_LOC_4_ENGLISH.json",
        help="Localization filename to process (default: NMS_LOC_4_ENGLISH.json)"
    )
    
    parser.add_argument(
        "--token-limit", "-tl",
        type=int,
        default=50000,
        help="Token limit per patch (default: 50000, safe for Gemini output limit)"
    )
    
    parser.add_argument(
        "--max-retries", "-mr",
        type=int,
        default=3,
        help="Maximum retry attempts (default: 3)"
    )
    
    parser.add_argument(
        "--list-workflows",
        action="store_true",
        help="List available workflow types and exit"
    )
    
    args = parser.parse_args()
    
    # List workflows and exit
    if args.list_workflows:
        print("Available workflow types:")
        print("  sequence       - Sequential execution of all patches")
        print("  full_parallel  - Parallel execution with max 3 concurrent patches")
        return
    
    # Validate input file exists
    loc_input_file = Path("input") / args.loc_filename
    if not loc_input_file.exists():
        print_error(f"Localization file not found: {loc_input_file}")
        print("Please place the file in the 'input/' directory!")
        sys.exit(1)
    
    # Print header
    print_header(args.wf_type, args.loc_filename)
    
    # Run workflow
    result = run_workflow(
        wf_type=args.wf_type,
        loc_filename=args.loc_filename,
        token_limit=args.token_limit,
        max_retries=args.max_retries
    )
    
    # Handle results
    if result["success"]:
        print_success("Translation completed successfully!")
        sys.exit(0)
    else:
        print_error(f"Translation failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
