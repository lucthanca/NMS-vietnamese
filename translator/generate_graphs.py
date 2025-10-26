#!/usr/bin/env python3
"""
Script để generate visualization graphs của workflows.
"""
from workflows.parallel_wf import create_parallel_workflow
from workflows.sequence_wf import create_sequence_workflow
from pathlib import Path

# Create output directory
output_dir = Path("graphs")
output_dir.mkdir(exist_ok=True)

print("📊 Generating workflow graphs...\n")

# Generate parallel workflow graph
print("1️⃣  Generating parallel workflow graph...")
try:
    parallel_wf = create_parallel_workflow()
    
    # Try to save PNG
    try:
        parallel_wf.get_graph(xray=True).draw_mermaid_png(
            output_file_path=str(output_dir / "parallel_workflow.png")
        )
        print(f"   ✅ Saved to {output_dir / 'parallel_workflow.png'}")
    except Exception as e:
        print(f"   ⚠️  PNG failed: {e}")
        # Fallback to mermaid text
        mermaid = parallel_wf.get_graph(xray=True).draw_mermaid()
        (output_dir / "parallel_workflow.mmd").write_text(mermaid, encoding="utf-8")
        print(f"   ✅ Saved mermaid to {output_dir / 'parallel_workflow.mmd'}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Generate sequential workflow graph
print("\n2️⃣  Generating sequential workflow graph...")
try:
    sequence_wf = create_sequence_workflow()
    
    # Try to save PNG
    try:
        sequence_wf.get_graph(xray=True).draw_mermaid_png(
            output_file_path=str(output_dir / "sequence_workflow.png")
        )
        print(f"   ✅ Saved to {output_dir / 'sequence_workflow.png'}")
    except Exception as e:
        print(f"   ⚠️  PNG failed: {e}")
        # Fallback to mermaid text
        mermaid = sequence_wf.get_graph(xray=True).draw_mermaid()
        (output_dir / "sequence_workflow.mmd").write_text(mermaid, encoding="utf-8")
        print(f"   ✅ Saved mermaid to {output_dir / 'sequence_workflow.mmd'}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ Graph generation completed!")
print(f"📁 Output directory: {output_dir.absolute()}")
