"""Gmail search query configuration for school-related emails."""

# Sender domains to match
SENDER_DOMAINS = [
    "mybrightwheel.com",
    "notify.mybrightwheel.com",
    "schoolsbuddy.com",
    "bischicagolp.org",
    "studentflow.io",
    "nordanglia.com",
]

# Keywords to match in subject/body
KEYWORDS = [
    "British International School",
    "BISC",
    "BISC-LP",
    "Hedgehog",
    "Lamb",
]


def build_gmail_query() -> str:
    """Build the Gmail search query string.

    Returns the query combining sender domain matches (OR) with keyword matches (OR).
    """
    from_clauses = " OR ".join(SENDER_DOMAINS)
    keyword_clauses = " OR ".join(f'"{kw}"' for kw in KEYWORDS)
    return f"from:({from_clauses}) OR ({keyword_clauses})"
