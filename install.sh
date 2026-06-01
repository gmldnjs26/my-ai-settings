#!/usr/bin/env bash
#
# my-ai-settings 설치 스크립트
# .claude/skills 의 스킬과 설정 파일을 ~/.claude 로 적용한다.
# 기존 설정 파일은 덮어쓰기 전에 .bak 으로 백업한다.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.claude"
DEST="$HOME/.claude"

echo "==> Claude 설정 디렉토리: $DEST"
mkdir -p "$DEST/skills"

# 1) 스킬 복사
echo "==> 스킬 설치"
for skill in "$SRC"/skills/*/; do
  name="$(basename "$skill")"
  target="$DEST/skills/$name"
  if [ -e "$target" ] || [ -L "$target" ]; then
    echo "    - $name (기존 항목 발견, 건너뜀)"
    continue
  fi
  cp -R "$skill" "$target"
  echo "    + $name 설치됨"
done

# 2) 설정 파일 복사 (백업 후 덮어쓰기)
echo "==> 설정 파일 적용"
for f in CLAUDE.md settings.json settings.local.json statusline.js; do
  [ -f "$SRC/$f" ] || continue
  if [ -f "$DEST/$f" ]; then
    cp "$DEST/$f" "$DEST/$f.bak"
    echo "    ~ $f (기존 파일 → $f.bak 으로 백업)"
  fi
  cp "$SRC/$f" "$DEST/$f"
  echo "    + $f 적용됨"
done

echo "==> 완료. Claude Code 를 재시작하면 적용됩니다."
