# Games Repository Assessments

This directory contains assessment prompts and results for the periodic evaluation of the Games repository.

## Assessment Framework

The Games repository uses a **three-assessment rotation cycle** designed to comprehensively evaluate different aspects of the codebase:

| Assessment | Focus Area                        | Primary Concerns                                                          |
| ---------- | --------------------------------- | ------------------------------------------------------------------------- |
| **A**      | Architecture & Implementation     | Game mechanics, engine design, completeness, performance                  |
| **B**      | Hygiene & Quality                 | Linting compliance, code organization, security, asset management         |
| **C**      | Documentation & Player Experience | Documentation, gameplay guides, asset documentation, launcher integration |

## Assessment Schedule

Assessments are designed to be run on a rotating daily schedule:

- **Day 1**: Assessment A (Architecture)
- **Day 2**: Assessment B (Hygiene)
- **Day 3**: Assessment C (Documentation)
- **Day 4**: Cycle repeats

## Directory Structure

```
docs/assessments/
├── README.md                          # This file
├── Assessment_Prompt_A.md             # Architecture & Implementation Assessment
├── Assessment_Prompt_B.md             # Hygiene & Quality Assessment
├── Assessment_Prompt_C.md             # Documentation & Player Experience Assessment
├── Documentation_Cleanup_Prompt.md    # Documentation improvement agent prompt
└── archive/                           # Historical assessment results
    └── Assessment_A_Results_YYYY-MM-DD.md
```

## Running Assessments

1. Select the appropriate assessment prompt based on the current rotation day
2. Provide the prompt to the AI agent along with repository access
3. Review the generated findings and prioritize remediation
4. Archive results with the date for tracking progress

## Key Reference Documents

- `AGENTS.md` - Agent coding standards and guidelines
- `JULES_ARCHITECTURE.md` - Agent architecture specification
- `README.md` - Repository overview and game listing
- `ruff.toml`, `mypy.ini` - Linting configuration

## Game Categories

| Category     | Examples            | Assessment Focus                              |
| ------------ | ------------------- | --------------------------------------------- |
| Pygame Games | Duum, Force Field   | Engine performance, game loop, asset pipeline |
| Web Games    | Browser-based       | HTML/CSS/JS quality, responsiveness           |
| Utilities    | Launcher, Sound Gen | Integration quality, usability                |

## Integration with CI/CD

Assessment findings should be converted to actionable items:

1. **Blockers/Critical**: Immediate PR creation required
2. **Major**: Short-term backlog items (2 weeks)
3. **Minor/Nit**: Long-term improvement tracking

## Pragmatic Programmer Principles Applied

- **DRY (Don't Repeat Yourself)**: Identify duplicated game mechanics
- **Orthogonality**: Evaluate module independence
- **Tracer Bullets**: Verify end-to-end game playability
- **Good Enough Software**: Balance polish with pragmatic delivery
- **Prototypes and Tracer Bullets**: Rapid iteration on gameplay
