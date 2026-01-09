# Out of Scope

These are enterprise/production concerns. **Ignore for this assignment.**

---

## Data Safety (Not Required)
- Atomic save with temp files
- Backup file creation
- File locking
- Encoding detection (UTF-8 is fine)
- BOM handling
- Line ending preservation

## Scalability (Not Required)
- Large file handling (100MB+)
- Streaming file loading
- Network path timeouts
- Symlink handling

## Architecture (Not Required for HW)
- Strict MVC separation
- Plugin architecture  
- Configuration management
- Thread safety
- Memory leak fixes (minor)

## Accessibility (Not Required)
- Screen reader support
- Accessibility labels

## Multi-Instance (Not Required)
- File locking across instances
- Single instance enforcement

---

**Why ignore these?**

These are real concerns for production software, but:
1. Assignment doesn't require them
2. Time is limited (2 weeks)
3. Won't be tested during demo
4. UTF-8 and basic save/open is sufficient for grading
