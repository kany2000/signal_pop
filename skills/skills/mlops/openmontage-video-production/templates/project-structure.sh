#!/usr/bin/env bash
# Project Structure Initialization for OpenMontage
# Usage: bash templates/project-structure.sh <kebab-case-project-name>

set -euo pipefail

PROJECT_NAME="${1:-}"
if [[ -z "$PROJECT_NAME" ]]; then
    echo "Usage: $0 <kebab-case-project-name>"
    echo "Example: $0 rainy-night-cinematic"
    exit 1
fi

BASE_DIR="/home/kan/shared/OpenMontage"
PROJECT_DIR="$BASE_DIR/projects/$PROJECT_NAME"

echo "Creating OpenMontage project structure for: $PROJECT_NAME"
echo "Location: $PROJECT_DIR"

mkdir -p "$PROJECT_DIR/artifacts"
mkdir -p "$PROJECT_DIR/assets/images"
mkdir -p "$PROJECT_DIR/assets/video"
mkdir -p "$PROJECT_DIR/assets/audio"
mkdir -p "$PROJECT_DIR/assets/music"
mkdir -p "$PROJECT_DIR/renders"

# Create a README for the project
cat > "$PROJECT_DIR/README.md" <<EOF
# $PROJECT_NAME

OpenMontage project created $(date '+%Y-%m-%d %H:%M').

## Structure
\`\`\`
$PROJECT_NAME/
├── artifacts/           # JSON artifacts from each stage
│   ├── research_brief.json
│   ├── proposal_packet.json
│   ├── script.json
│   ├── scene_plan.json
│   ├── asset_manifest.json
│   ├── edit_decisions.json
│   └── render_report.json
├── assets/
│   ├── images/          # Generated images (PNG)
│   ├── video/           # Generated video clips (MP4)
│   ├── audio/           # Narration + final mix (MP3/WAV)
│   └── music/           # Background music (MP3)
└── renders/
    └── final.mp4        # Final deliverable
\`\`\`

## Pipeline
TBD - fill in after proposal approval.

## Decisions Log
- Render runtime: TBD
- Animation mode: TBD
- Budget approved: TBD
EOF

echo "✅ Project structure created at $PROJECT_DIR"
echo ""
echo "Next steps:"
echo "1. Run capability discovery:"
echo "   cd $BASE_DIR && python -c \"from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.provider_menu_summary(), indent=2))\""
echo "2. Select pipeline based on brief"
echo "3. Begin research stage"