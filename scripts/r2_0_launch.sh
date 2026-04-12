#!/bin/bash
set -e

echo "=== R2.0 Pre-launch ==="

# Commit current state
git add -A
git commit -m "R2.0: logging flags, regression tests passing" || echo "Nothing to commit"
git tag -f r2.0-baseline

# Create revision branch if not already on it
git checkout -b revision 2>/dev/null || echo "Already on revision branch or branch exists"

# Capture results/ baseline for post-run integrity check
find results/ -type f -exec stat -c "%n %Y %s" {} + | sort > /tmp/results_baseline.txt
echo "Baseline captured: $(wc -l < /tmp/results_baseline.txt) files in results/"

# Ensure output dirs exist
mkdir -p results_new/trajectories results_new/collisions

echo ""
echo "=== Ready. Now launch R2.0 in tmux: ==="
echo "  tmux new -s r2_run"
echo "  python new_experiments/r2_logging_run.py 2>&1 | tee results_new/r2_run.log"
echo "  # detach with Ctrl-b, d"
echo ""
echo "Check progress:  tmux attach -t r2_run"
echo "Expected wall-clock: ~22-24 hours"
