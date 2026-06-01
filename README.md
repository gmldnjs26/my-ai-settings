# my-ai-settings

내 Claude Code 설정과 스킬(skills)을 한곳에 모아 다른 환경에서도 쉽게 적용하기 위한 리포지토리.

## 구조

```
.claude/
├── CLAUDE.md            # 전역 사용자 지침
├── settings.json        # 권한, 훅, 스테이터스라인, 플러그인, 규칙 등
├── settings.local.json  # 로컬 권한 설정
├── statusline.js        # 커스텀 스테이터스라인
└── skills/              # 설치된 스킬 모음
    ├── obsidian-excalidraw/        # Obsidian Excalidraw 다이어그램 생성/편집
    ├── figma-frame-reader/         # Figma 페이지 프레임 단위 읽기
    ├── git-workflow/               # 커밋/푸시/PR (Conventional Commits)
    ├── skill-creator/              # 새 스킬 생성 가이드
    ├── find-skills/                # 스킬 검색/설치
    ├── vercel-composition-patterns/
    ├── vercel-react-best-practices/
    ├── vercel-react-native-skills/
    └── web-design-guidelines/
```

## 적용 방법

### 전체 설치 (스킬 + 설정)

```bash
git clone https://github.com/gmldnjs26/my-ai-settings.git
cd my-ai-settings
./install.sh
```

`install.sh`는 `.claude/skills/` 안의 스킬을 `~/.claude/skills/`로 복사하고,
설정 파일은 기존 파일을 덮어쓰기 전에 백업(`*.bak`)을 남깁니다.

### 스킬만 추가하기

특정 스킬만 다른 환경에 추가하려면 해당 디렉토리를 `~/.claude/skills/`로 복사하면 됩니다.

```bash
cp -R .claude/skills/obsidian-excalidraw ~/.claude/skills/
```

복사 후 Claude Code를 재시작하면 스킬이 인식됩니다.
