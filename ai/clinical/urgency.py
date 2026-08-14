def get_urgency(symptoms):
    """Placeholder urgency checking based on extracted symptoms."""
    # Simple heuristic
    urgent_keywords = ["chest pain", "bleeding", "unconscious", "shortness of breath", "severe"]
    for sym in symptoms:
        if any(urgent in sym.lower() for urgent in urgent_keywords):
            return "critical"
    return "routine"
