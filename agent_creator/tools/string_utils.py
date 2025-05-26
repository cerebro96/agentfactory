def _break_long_line(text: str, max_length: int = 120) -> list:
    """Breaks a long line into multiple parts at logical breaking points."""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    remaining = text
    
    while remaining:
        if len(remaining) <= max_length:
            parts.append(remaining)
            break
        
        # Check if we have a \n at the end that we need to preserve
        has_newline_at_end = remaining.endswith('\\n')
        
        # Find the last space within max_length
        # If we have \n at the end, reduce max_length by 2 to ensure it fits
        effective_max_length = max_length - 2 if has_newline_at_end else max_length
        break_point = remaining[:effective_max_length].rfind(' ')
        
        if break_point == -1:
            # No space found, try to break at punctuation
            for i in range(effective_max_length - 1, 0, -1):
                if remaining[i] in ',.;:!?-':
                    break_point = i + 1
                    break
        
        if break_point == -1:
            # Still no good break point, force break at effective_max_length
            break_point = effective_max_length
        
        # Add the part and continue with the rest
        parts.append(remaining[:break_point].rstrip())
        remaining = remaining[break_point:].lstrip()
    
    return parts 