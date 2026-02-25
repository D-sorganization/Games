# Completist Report: 2026-02-24

**Score**: 7/10

## Summary

Total issues found: 34

### Abstract Methods: 6
Sample:
- ./scripts/analyze_completist_data.py:185:        if f_path and l_no and c_txt and "@abstractmethod" in c_txt:
- ./scripts/analyze_completist_data.py-186-            return Finding(file=f_path, line=l_no, text=c_txt, type="Abstract")
- ./scripts/analyze_completist_data.py-187-        return None
- ./scripts/analyze_completist_data.py-188-
- ./scripts/analyze_completist_data.py-189-    return _scan_completist_file("ABSTRACT", _parser)

### Incomplete Docs: 0

### Not Implemented: 5
Sample:
- ./scripts/analyze_completist_data.py:207:        "NotImplementedError": 4,
- ./scripts/shared/quality_checks_common.py:13:    (re.compile(r"NotImplementedError"), "NotImplementedError placeholder"),
- ./src/games/Zombie_Survival/src/bot.py:400:                    pass  # Check Y later
- ./src/games/Duum/src/bot.py:418:                    pass  # Check Y later
- ./src/games/shared/spawn_manager.py:98:        raise NotImplementedError("Subclasses must implement _make_bot")

### Todo Markers: 23
Sample:
- ./constants_file.py:37:TEMPERATURE_C: float = 20.0  # [°C] Standard temperature
- ./scripts/analyze_completist_data.py:106:    fixme_markers = ["FIX" + "ME", "XXX", "HACK", "TEMP"]
- ./scripts/shared/quality_checks_common.py:10:    (re.compile(r"\bTODO\b"), "TODO placeholder found"),
- ./scripts/shared/quality_checks_common.py:11:    (re.compile(r"\bFIXME\b"), "FIXME placeholder found"),
- ./src/games/shared/constants.py:153:BOT_SPAWN_ATTEMPTS = 20
