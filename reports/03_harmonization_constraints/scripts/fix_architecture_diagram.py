#!/usr/bin/env python3
"""
Generate corrected architecture_pipeline.png showing ALL pairs go to arbitration.

CRITICAL FIX: The old diagram incorrectly showed only disagreements going to 
arbitration. In reality, ALL 1,598 pairs were sent to ALL arbitrators to 
enable full behavioral analysis.

Usage:
    python scripts/fix_architecture_diagram.py
"""
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).parent.parent
OUTPUT = BASE / "presentation/images/architecture_pipeline.png"

# Correct architecture: ALL pairs go to both rating AND arbitration
MERMAID_SRC = '''
flowchart TB
    subgraph Input["Input Data"]
        pairs["1,598 Question Pairs<br/>(CPS-ACS, FoodAPS-ACS)"]
    end
    
    subgraph Stage1["Stage 1: Rating<br/>(Fast Models)"]
        direction TB
        r1["OpenAI gpt-4o-mini"]
        r2["Anthropic claude-haiku-4-5"]
        r3["Google gemini-2-flash"]
    end
    
    subgraph Stage3["Stage 3: Arbitration<br/>(Flagship Models)"]
        direction TB
        a1["OpenAI GPT-5.2"]
        a2["Anthropic Claude Opus 4.5"]
        a3["Google Gemini 3 Pro"]
    end
    
    subgraph Stage2["Stage 2: Agreement Analysis"]
        agree["Inter-Rater Metrics<br/>κ = 0.611"]
    end
    
    subgraph Stage4["Stage 4: Findings"]
        rollup["Question-Level Rollup<br/>380 unique questions<br/>Best-match selection"]
    end
    
    subgraph Stage5["Stage 5: Deliverables"]
        deliver["Expert Review Tables<br/>Triage Assignments"]
    end
    
    pairs --> Stage1
    pairs --> Stage3
    
    Stage1 --> Stage2
    Stage3 --> Stage4
    Stage2 -.->|"Metrics inform<br/>validation"| Stage4
    
    Stage4 --> Stage5
    
    note1["Note: Stage 1 and Stage 3<br/>can run in parallel"]
    
    style Input fill:#e1f5fe
    style Stage1 fill:#e8f5e9
    style Stage2 fill:#fff3e0
    style Stage3 fill:#fce4ec
    style Stage4 fill:#f3e5f5
    style Stage5 fill:#e0f2f1
'''

def main():
    print("Generating corrected architecture diagram...")
    print(f"Output: {OUTPUT}")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(MERMAID_SRC)
        mmd_path = f.name
    
    try:
        # -s 3 for scale, -w 1200 for width
        result = subprocess.run(
            ['mmdc', '-i', mmd_path, '-o', str(OUTPUT), '-b', 'white', '-s', '3', '-w', '1200'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"[OK] Created {OUTPUT}")
        else:
            print(f"[ERROR] mmdc failed: {result.stderr}")
            print("Install with: npm install -g @mermaid-js/mermaid-cli")
    except FileNotFoundError:
        print("[ERROR] mmdc not found")
        print("Install with: npm install -g @mermaid-js/mermaid-cli")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
