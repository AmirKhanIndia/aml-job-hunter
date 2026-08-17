import re
from html import unescape

from workers import fetch


COMPANIES = {
    "Stripe": "stripe",
    "Coinbase": "coinbase",
    "NICE": "nice",
    "Robinhood": "robinhood",
}


INDIA_LOCATIONS = [
    "india",
    "new delhi",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "bangalore",
    "bengaluru",
    "mumbai",
    "hyderabad",
    "pune",
    "chennai",
    "kolkata",
    "ahmedabad",
    "jaipur",
    "chandigarh",
    "kochi",
    "indore",
    "lucknow",
]


INDIA_REMOTE_PHRASES = [
    "remote india",
    "remote - india",
    "remote, india",
    "india remote",
    "india - remote",
    "work from home india",
    "work from home - india",
    "work from home, india",
    "anywhere in india",
    "pan india",
    "pan-india",
]


ROLE_KEYWORDS = {
    "AML": [
        "aml analyst",
        "aml investigator",
        "aml specialist",
        "aml officer",
        "aml associate",
        "aml operations",
        "anti money laundering",
        "anti-money laundering",
    ],

    "KYC": [
        "kyc analyst",
        "kyc investigator",
        "kyc specialist",
        "kyc officer",
        "kyc associate",
        "kyc operations",
        "know your customer",
    ],

    "Transaction Monitoring": [
        "transaction monitoring",
        "transaction monitoring analyst",
        "transaction monitoring investigator",
        "transaction monitoring specialist",
        "transaction monitoring associate",
        "transaction monitoring officer",
    ],

    "Financial Crime": [
        "financial crime analyst",
        "financial crime investigator",
        "financial crime specialist",
        "financial crime associate",
        "financial crime officer",
        "financial crime operations",
        "financial crimes",
    ],

    "Fraud": [
        "fraud analyst",
        "fraud investigator",
        "fraud specialist",
        "fraud operations",
        "fraud operations associate",
        "fraud prevention",
        "fraud risk",
        "fraud detection",
        "payments fraud",
    ],

    "Sanctions": [
        "sanctions analyst",
        "sanctions investigator",
        "sanctions specialist",
        "sanctions officer",
        "sanctions screening",
        "sanctions operations",
    ],

    "Risk Investigation": [
        "risk investigator",
        "transaction risk investigator",
        "transaction risk",
        "risk operations analyst",
        "risk operations associate",
        "risk operations",
    ],

    "CDD/EDD": [
        "cdd analyst",
        "cdd investigator",
        "edd analyst",
        "edd investigator",
        "customer due diligence",
        "enhanced due diligence",
        "due diligence",
    ],

    "Compliance": [
        "compliance analyst",
        "compliance investigator",
        "compliance specialist",
        "compliance operations",
        "compliance associate",
        "financial compliance",
    ],

    "Trust & Safety": [
        "trust and safety",
        "trust & safety",
        "trust safety",
        "safety investigator",
        "trust investigator",
        "content risk investigator",
    ],

    "Payments Risk": [
        "payments risk",
        "payment risk",
        "payments investigator",
        "payments operations",
        "payment operations",
        "payment fraud",
    ],
}


PROFILE_SKILLS = [
    "aml",
    "kyc",
    "transaction monitoring",
    "financial crime",
    "fraud investigation",
    "fraud detection",
    "fraud operations",
    "risk investigation",
    "transaction risk",
    "customer due diligence",
    "enhanced due diligence",
    "sanctions",
    "sanctions screening",
    "compliance",
    "investigation",
    "case investigation",
    "case management",
    "identity verification",
    "customer verification",
    "customer screening",
    "name screening",
    "watchlist screening",
    "suspicious activity",
    "suspicious activity report",
    "sar",
    "risk assessment",
    "customer risk",
    "fraud risk",
    "transaction analysis",
    "payments risk",
    "trust and safety",
]


EXCLUDED_TITLE_KEYWORDS = [
    "sales",
    "marketing",
    "software engineer",
    "software developer",
    "frontend",
    "backend",
    "full stack",
    "accountant",
    "accounting",
    "fp&a",
    "product manager",
    "product designer",
    "graphic designer",
    "recruiter",
    "developer",
    "data scientist",
    "machine learning engineer",
    "data engineer",
    "customer success",
    "business development",
    "account executive",
    "sales development",
    "relationship manager",
    "investment banking",
    "financial advisor",
    "tax accountant",
    "credit analyst",
    "underwriter",
    "underwriting",
    "market risk",
    "enterprise risk",
    "internal auditor",
    "internal audit",
]


EXPERIENCE_KEYWORDS = [
    "investigation",
    "case investigation",
    "case management",
    "transaction monitoring",
    "financial crime",
    "aml",
    "kyc",
    "fraud investigation",
    "risk investigation",
    "customer due diligence",
    "enhanced due diligence",
    "sanctions screening",
    "customer screening",
    "watchlist screening",
    "suspicious activity",
    "identity verification",
    "fraud detection",
    "payments risk",
    "trust and safety",
]


def clean_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "").lower(),
    ).strip()


def get_location(job):
    location = job.get("location", {})

    if isinstance(location, dict):
        return str(location.get("name", ""))

    return str(location)


def classify_location(location):
    location_lower = normalize(location)

    if not location_lower:
        return "UNKNOWN"

    for phrase in INDIA_REMOTE_PHRASES:
        if phrase in location_lower:
            return "INDIA_REMOTE"

    for city in INDIA_LOCATIONS:
        if city in location_lower:
            return "INDIA"

    return "OTHER"


def location_score(location_type):
    if location_type == "INDIA":
        return 15

    if location_type == "INDIA_REMOTE":
        return 20

    return 0


async def fetch_greenhouse_jobs(
    company_name,
    board_token,
):
    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        + board_token
        + "/jobs?content=true"
    )

    try:
        response = await fetch(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": "AML-Job-Hunter/1.0",
            },
        )

        if response.status != 200:
            print(
                "Skipped:",
                company_name,
                "| HTTP",
                response.status,
            )
            return []

        data = await response.json()

        jobs = data.get("jobs", [])

        print(
            "Jobs found:",
            len(jobs),
        )

        for job in jobs:
            job["_company"] = company_name

        return jobs

    except Exception as error:
        print(
            "Error:",
            company_name,
            "|",
            str(error),
        )
        return []


def find_roles(title, description):
    matched_roles = []

    combined = (
        normalize(title)
        + " "
        + normalize(description)
    )

    for role, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in combined:

                if role not in matched_roles:
                    matched_roles.append(role)

                break

    return matched_roles


def calculate_score(
    title,
    description,
    location_type,
    matched_roles,
):
    title_lower = normalize(title)
    description_lower = normalize(description)

    score = 0

    # Location
    score += location_score(location_type)

    # Role relevance
    if matched_roles:
        score += min(
            len(matched_roles) * 20,
            40,
        )

    # Strong title relevance
    for role, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title_lower:
                score += 15
                break

    # Profile skills
    skill_matches = []

    for skill in PROFILE_SKILLS:

        if skill in title_lower:
            score += 4

            if skill not in skill_matches:
                skill_matches.append(skill)

        elif skill in description_lower:
            score += 2

            if skill not in skill_matches:
                skill_matches.append(skill)

    score = min(score, 100)

    return score, skill_matches


async def scan_jobs():

    all_jobs = []

    print()
    print("========================================")
    print("       AML / KYC CLOUD JOB HUNTER")
    print("========================================")

    for company_name, board_token in COMPANIES.items():

        print()
        print("Scanning:", company_name)

        jobs = await fetch_greenhouse_jobs(
            company_name,
            board_token,
        )

        all_jobs.extend(jobs)

    print()
    print("========================================")
    print("             FILTERING")
    print("========================================")

    print(
        "Total jobs collected:",
        len(all_jobs),
    )

    location_candidates = 0
    role_candidates = 0

    matched_jobs = []

    for job in all_jobs:

        title = job.get("title", "")
        content = job.get("content", "")
        location = get_location(job)

        description = clean_html(content)

        title_lower = normalize(title)

        # Exclude clearly irrelevant titles
        excluded = False

        for keyword in EXCLUDED_TITLE_KEYWORDS:

            if keyword in title_lower:
                excluded = True
                break

        if excluded:
            continue

        # Location
        location_type = classify_location(location)

        if location_type not in [
            "INDIA",
            "INDIA_REMOTE",
        ]:
            continue

        location_candidates += 1

        # Role matching
        matched_roles = find_roles(
            title,
            description,
        )

        if not matched_roles:
            continue

        role_candidates += 1

        # Score
        score, matched_skills = calculate_score(
            title,
            description,
            location_type,
            matched_roles,
        )

        # Only useful matches
        if score < 50:
            continue

        experience_matches = []

        description_lower = normalize(
            description
        )

        for keyword in EXPERIENCE_KEYWORDS:

            if keyword in description_lower:

                if keyword not in experience_matches:
                    experience_matches.append(
                        keyword
                    )

        matched_jobs.append(
            {
                "job": job,
                "score": score,
                "matched_roles": matched_roles,
                "matched_skills": matched_skills,
                "experience_matches": experience_matches,
                "location_type": location_type,
            }
        )

    matched_jobs.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    print()
    print("========================================")
    print("              RESULTS")
    print("========================================")

    print(
        "Total jobs scanned:",
        len(all_jobs),
    )

    print(
        "India location candidates:",
        location_candidates,
    )

    print(
        "Role candidates:",
        role_candidates,
    )

    print(
        "Qualified jobs:",
        len(matched_jobs),
    )

    for number, result in enumerate(
        matched_jobs,
        start=1,
    ):

        job = result["job"]

        print()
        print("----------------------------------------")

        print(
            "#",
            number,
        )

        print(
            "Company:",
            job.get("_company"),
        )

        print(
            "Job Title:",
            job.get("title"),
        )

        print(
            "Location:",
            get_location(job),
        )

        print(
            "Match Score:",
            str(result["score"]) + "/100",
        )

        print(
            "Matched Roles:",
            ", ".join(
                result["matched_roles"]
            ),
        )

        print(
            "Profile Skills:",
            ", ".join(
                result["matched_skills"]
            )
            if result["matched_skills"]
            else "None",
        )

        print(
            "Experience:",
            ", ".join(
                result["experience_matches"]
            )
            if result["experience_matches"]
            else "None",
        )

        print(
            "URL:",
            job.get("absolute_url"),
        )

    print()
    print("========================================")
    print("          CLOUD SCAN COMPLETED")
    print("========================================")

    return matched_jobs