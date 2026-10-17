import re

def validate_and_clean_mermaid(mermaid_code: str) -> str:
    """
    Cleans up Mermaid diagram markdown ticks and ensures valid diagram keywords.
    """
    if not mermaid_code:
        return "graph TD\n    A[Core Concept] --> B[Implementation]\n    B --> C[Real World Outcome]"
    
    # Strip markdown code blocks if present
    code = mermaid_code.strip()
    if code.startswith("```"):
        code = re.sub(r"^```(?:mermaid)?\n?", "", code)
        code = re.sub(r"\n?```$", "", code)
    code = code.strip()

    valid_headers = ["graph TD", "graph LR", "graph TB", "flowchart TD", "flowchart LR", "mindmap", "sequenceDiagram", "classDiagram"]
    has_header = any(code.startswith(h) for h in valid_headers)
    
    if not has_header:
        code = f"graph TD\n{code}"
    
    return code

def generate_default_diagram(lesson_title: str, key_ideas: list) -> str:
    """
    Generates a high-quality flowchart/mindmap if AI output needs a guaranteed clean diagram.
    """
    clean_title = re.sub(r'[^a-zA-Z0-9 ]', '', lesson_title)[:25]
    step1 = re.sub(r'[^a-zA-Z0-9 ]', '', key_ideas[0] if len(key_ideas) > 0 else "Foundation")[:30]
    step2 = re.sub(r'[^a-zA-Z0-9 ]', '', key_ideas[1] if len(key_ideas) > 1 else "Core Mechanism")[:30]
    step3 = re.sub(r'[^a-zA-Z0-9 ]', '', key_ideas[2] if len(key_ideas) > 2 else "Optimal Impact")[:30]

    return f"""graph LR
    A["{clean_title}"] --> B["{step1}"]
    B --> C["{step2}"]
    C --> D["{step3}"]
    style A fill:#0A66C2,stroke:#0A66C2,color:#FFFFFF,stroke-width:2px
    style B fill:#EBF3FA,stroke:#0A66C2,color:#191919,stroke-width:1px
    style C fill:#EBF3FA,stroke:#0A66C2,color:#191919,stroke-width:1px
    style D fill:#057642,stroke:#057642,color:#FFFFFF,stroke-width:2px"""
