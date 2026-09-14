def build_explanation(tier, contributors, occupied, adaptive_reason=None):
    top = contributors[:3]
    if not top:
        return f"{tier} risk; insufficient feature contribution data."
    names = ", ".join(item["feature"] for item in top)
    occupancy_text = "occupancy confirmed" if occupied else "no occupancy detected"
    base = f"{tier} risk is mainly influenced by {names}; {occupancy_text}."
    return f"{base} {adaptive_reason}." if adaptive_reason else base
