#!/bin/bash
# Helper script to copy project files to data/raw

echo "Copying project files to data/raw..."

# Project files are typically in /mnt/project/
if [ -f "/mnt/project/PublicSurveyQuestions.csv" ]; then
    cp /mnt/project/PublicSurveyQuestions.csv data/raw/
    echo "✓ Copied PublicSurveyQuestions.csv"
else
    echo "⚠ PublicSurveyQuestions.csv not found in /mnt/project/"
    echo "Please manually copy the file to data/raw/"
fi

if [ -f "/mnt/project/Canonical_JSON_Format_for_Survey_Question_Analysis.txt" ]; then
    cp "/mnt/project/Canonical_JSON_Format_for_Survey_Question_Analysis.txt" data/reference/
    echo "✓ Copied Canonical JSON format document"
fi

echo "Done!"
