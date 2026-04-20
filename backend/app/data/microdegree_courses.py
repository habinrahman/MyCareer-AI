"""
MicroDegree course catalog.

Role-keyed lists feed learning-path recommendations; titles use the
``Course Name — MicroDegree`` format (no pricing or tiers).
"""

MICRODEGREE_COURSES: dict[str, list[str]] = {
    "DevOps Engineer": [
        "DevOps Engineering — MicroDegree",
        "DevSecOps — MicroDegree",
        "Certified Kubernetes Administrator (CKA/CKAD) — MicroDegree",
        "Azure DevOps Engineer — MicroDegree",
        "Linux & Networking — MicroDegree",
    ],
    "Site Reliability Engineer": [
        "DevOps Engineering — MicroDegree",
        "Certified Kubernetes Administrator (CKA/CKAD) — MicroDegree",
        "Linux & Networking — MicroDegree",
        "Cloud AI Fundamentals — MicroDegree",
    ],
    "Cloud Engineer": [
        "AWS Solutions Architect — MicroDegree",
        "Microsoft Azure Solutions Architect — MicroDegree",
        "Google Cloud Platform (GCP) — MicroDegree",
        "Cloud AI Fundamentals — MicroDegree",
    ],
    "Infrastructure Engineer": [
        "Linux & Networking — MicroDegree",
        "AWS Solutions Architect — MicroDegree",
        "Microsoft Azure Solutions Architect — MicroDegree",
        "Google Cloud Platform (GCP) — MicroDegree",
    ],
    "Automation Engineer": [
        "DevOps Engineering — MicroDegree",
        "Azure DevOps Engineer — MicroDegree",
        "Prompt Engineering — MicroDegree",
    ],
    "AI Engineer": [
        "Cloud AI Fundamentals — MicroDegree",
        "Generative AI for Cloud & DevOps — MicroDegree",
        "Prompt Engineering — MicroDegree",
        "MLOps — MicroDegree",
    ],
    "Machine Learning Engineer": [
        "Cloud AI Fundamentals — MicroDegree",
        "Generative AI for Cloud & DevOps — MicroDegree",
        "MLOps — MicroDegree",
    ],
}
