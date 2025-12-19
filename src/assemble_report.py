#!/usr/bin/env python3
"""
Assemble the complete report from individual sections.
"""

from pathlib import Path
from datetime import datetime

# Paths
SECTIONS_DIR = Path('../final_report/sections')
OUTPUT_FILE = Path('../final_report/FULL_REPORT.md')

# Section order
SECTIONS = [
    '01_abstract.md',
    '02_introduction.md',
    '03_background.md',
    '04_methodology.md',
    '05_data_collection.md',
    '06_categorization_approach.md',
    '07_results.md',
    '08_coverage_analysis.md',
    '09_consolidation_opportunities.md',
    '10_discussion.md',
    '11_limitations.md',
    '12_recommendations.md',
    '13_conclusion.md',
    '14_appendices.md'
]

def assemble_report():
    """Assemble all sections into complete report."""
    
    print("Assembling Federal Survey Concept Mapping Report...")
    print("="*70)
    
    # Start with title page
    content = []
    content.append("# AI-Assisted Concept Mapping of Federal Survey Questions")
    content.append("## A Scalable Approach to Survey Taxonomy Analysis")
    content.append("")
    content.append("---")
    content.append("")
    content.append(f"**Report Date**: {datetime.now().strftime('%B %d, %Y')}")
    content.append("**Project**: Federal Survey Concept Mapping Study")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## Document Information")
    content.append("")
    content.append("- **Total Questions Analyzed**: 6,987")
    content.append("- **Federal Surveys Covered**: 46")
    content.append("- **Taxonomy**: Census Bureau Official (5 topics, 152 subtopics)")
    content.append("- **Methodology**: Dual-LLM categorization with arbitration")
    content.append("- **Success Rate**: 99.5%")
    content.append("- **Processing Time**: ~3 hours")
    content.append("- **Cost**: ~$15")
    content.append("")
    content.append("---")
    content.append("")
    content.append("\\newpage")
    content.append("")
    
    # Append each section
    for i, section_file in enumerate(SECTIONS, 1):
        section_path = SECTIONS_DIR / section_file
        
        if not section_path.exists():
            print(f"⚠️  WARNING: {section_file} not found!")
            continue
        
        print(f"  [{i:2d}/14] Adding {section_file}...")
        
        with open(section_path, 'r', encoding='utf-8') as f:
            section_content = f.read()
        
        content.append(section_content)
        content.append("")
        content.append("\\newpage")
        content.append("")
    
    # Write assembled report
    full_content = '\n'.join(content)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print("\n" + "="*70)
    print("REPORT ASSEMBLY COMPLETE!")
    print("="*70)
    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"Sections assembled: {len(SECTIONS)}")
    print(f"Total length: {len(full_content):,} characters")
    print(f"Estimated pages: ~{len(full_content) // 3000} pages")
    print("\nThe report is ready for review!")

if __name__ == '__main__':
    assemble_report()
