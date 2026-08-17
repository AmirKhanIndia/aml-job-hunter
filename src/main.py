import requests
import re
from html import unescape

COMPANIES = {
    "Greenhouse Demo": "greenhouse",
    "Stripe": "stripe",
    "Coinbase": "coinbase",
    "NICE": "nice",
    "Interactive Brokers": "ibkr",
    "Robinhood": "robinhood"
}

TARGET_ROLES = {
    "AML": [
        "aml analyst",
        "aml investigator",
        "aml specialist",
        "aml officer",
        "aml associate",
        "aml operations",
        "anti money laundering analyst",
        "anti-money laundering analyst"
    ],

    "KYC": [
        "kyc analyst",
        "kyc investigator",
        "kyc specialist",
        "kyc officer",
        "kyc associate",
        "kyc operations",
        "know your customer analyst"
    ],

    "Transaction Monitoring": [
        "transaction monitoring analyst",
        "transaction monitoring investigator",
        "transaction monitoring specialist",
        "transaction monitoring associate",
        "transaction monitoring officer"
    ],

    "Financial Crime": [
        "financial crime analyst",
        "financial crime investigator",
        "financial crime specialist",
        "financial crime associate",
        "financial crime officer",
        "financial crimes analyst",
        "financial crimes investigator",
        "financial crime operations"
    ],

    "Fraud": [
        "fraud analyst",
        "fraud investigator",
        "fraud specialist",
        "fraud operations",
        "fraud operations associate",
        "fraud prevention analyst",
        "fraud risk analyst",
        "payments fraud investigator"
    ],

    "Sanctions": [
        "sanctions analyst",
        "sanctions investigator",
        "sanctions specialist",
        "sanctions officer",
        "sanctions screening",
        "sanctions operations"
    ],

    "Risk Investigation": [
        "risk investigator",
        "transaction risk investigator",
        "risk operations analyst",
        "risk operations associate"
    ],

    "CDD/EDD": [
        "cdd analyst",
        "cdd investigator",
        "edd analyst",
        "edd investigator",
        "customer due diligence analyst",
        "customer due diligence investigator",
        "enhanced due diligence analyst",
        "enhanced due diligence investigator"
    ]
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
    "transaction analysis"
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
    "technical consulting",
    "technical consultant",
    "enablement",
    "business development",
    "account executive",
    "sales development",
    "relationship manager",
    "investment banking",
    "financial advisor",
    "tax",
    "tax compliance",
    "indirect tax",
    "income tax",
    "corporate tax",
    "credit risk",
    "credit analyst",
    "underwriter",
    "underwriting",
    "market risk",
    "enterprise risk",
    "operational risk manager",
    "hr compliance",
    "employment compliance",
    "privacy compliance",
    "product compliance",
    "internal auditor",
    "internal audit",
    "audit manager"
]

INDIA_WFO_LOCATIONS = [
    "delhi",
    "new delhi",
    "gurgaon",
    "gurugram",
    "noida"
]

INDIA_REMOTE_PHRASES = [
    "remote - india",
    "remote, india",
    "remote india",
    "india - remote",
    "india remote",
    "work from home - india",
    "work from home, india",
    "work from home india",
    "anywhere in india",
    "pan india",
    "pan-india",
    "india remote"
]

FOREIGN_COUNTRIES = [
    "united states",
    "usa",
    "u.s.",
    "us-remote",
    "us remote",
    "remote-us",
    "remote usa",
    "canada",
    "united kingdom",
    "uk",
    "ireland",
    "singapore",
    "cyprus",
    "luxembourg",
    "mexico",
    "australia",
    "germany",
    "france",
    "netherlands",
    "japan",
    "spain",
    "portugal",
    "italy",
    "switzerland",
    "poland",
    "brazil",
    "argentina",
    "israel",
    "uae",
    "dubai",
    "hong kong",
    "south korea",
    "czech",
    "czechia",
    "romania"
]


def clean_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def get_location(job):

    location = job.get("location", {})

    if isinstance(location, dict):
        return location.get("name", "")

    return str(location)


def classify_location(location):

    location_lower = normalize(location)

    if not location_lower:
        return "UNKNOWN"

    # Foreign location always wins
    for country in FOREIGN_COUNTRIES:
        if country in location_lower:
            return "FOREIGN"

    # Delhi / Gurgaon / Noida
    for city in INDIA_WFO_LOCATIONS:
        if city in location_lower:
            return "INDIA_WFO"

    # Explicit India remote
    for phrase in INDIA_REMOTE_PHRASES:
        if phrase in location_lower:
            return "INDIA_REMOTE"

    # Generic remote is NOT assumed to be India
    if "remote" in location_lower:
        return "REMOTE_UNKNOWN"

    if "work from home" in location_lower:
        return "REMOTE_UNKNOWN"

    return "OTHER"


def location_score(location_type):

    if location_type == "INDIA_WFO":
        return 15

    if location_type == "INDIA_REMOTE":
        return 15

    return 0


all_jobs = []

print()
print("========================================")
print("          AML / KYC JOB HUNTER")
print("========================================")

for company_name, board_token in COMPANIES.items():

    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        + board_token
        + "/jobs?content=true"
    )

    print()
    print("Scanning:", company_name)

    try:

        response = requests.get(
            url,
            timeout=30
        )

        if response.status_code != 200:

            print(
                "Skipped:",
                company_name,
                "| HTTP",
                response.status_code
            )

            continue

        data = response.json()

        jobs = data.get("jobs", [])

        print(
            "Jobs found:",
            len(jobs)
        )

        for job in jobs:

            job["_company"] = company_name
            all_jobs.append(job)

    except Exception as error:

        print(
            "Error:",
            company_name,
            "|",
            error
        )


matched_jobs = []

for job in all_jobs:

    title = job.get("title", "")
    content = job.get("content", "")
    location = get_location(job)

    clean_content = clean_html(content)

    title_lower = normalize(title)
    description_lower = normalize(clean_content)

    # --------------------------------------------------------
    # EXCLUDE IRRELEVANT TITLES
    # --------------------------------------------------------

    excluded = False

    for keyword in EXCLUDED_TITLE_KEYWORDS:

        if keyword in title_lower:
            excluded = True
            break

    if excluded:
        continue

    # --------------------------------------------------------
    # LOCATION FILTER
    # --------------------------------------------------------

    location_type = classify_location(location)

    # Only Delhi/Gurgaon/Noida WFO
    # OR explicitly India remote
    if location_type not in [
        "INDIA_WFO",
        "INDIA_REMOTE"
    ]:
        continue

    # --------------------------------------------------------
    # TARGET ROLE MATCH
    # --------------------------------------------------------

    matched_roles = []

    for role, keywords in TARGET_ROLES.items():

        for keyword in keywords:

            if keyword in title_lower:

                if role not in matched_roles:
                    matched_roles.append(role)

                break

    # Target role must be in the title
    if not matched_roles:
        continue

    # --------------------------------------------------------
    # TITLE SCORE
    # --------------------------------------------------------

    title_score = min(
        len(matched_roles) * 50,
        60
    )

    # --------------------------------------------------------
    # PROFILE SKILL MATCH
    # --------------------------------------------------------

    matched_skills = []
    skill_score = 0

    for skill in PROFILE_SKILLS:

        if skill in title_lower:

            skill_score += 5

            if skill not in matched_skills:
                matched_skills.append(skill)

        elif skill in description_lower:

            skill_score += 2

            if skill not in matched_skills:
                matched_skills.append(skill)

    skill_score = min(
        skill_score,
        25
    )

    # --------------------------------------------------------
    # EXPERIENCE MATCH
    # --------------------------------------------------------

    experience_keywords = [
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
        "suspicious activity"
    ]

    experience_matches = []
    experience_score = 0

    for keyword in experience_keywords:

        if keyword in description_lower:

            experience_score += 1

            if keyword not in experience_matches:
                experience_matches.append(keyword)

    experience_score = min(
        experience_score,
        15
    )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    score = (
        title_score
        + skill_score
        + experience_score
        + location_score(location_type)
    )

    score = min(
        score,
        100
    )

    matched_jobs.append({
        "job": job,
        "score": score,
        "matched_roles": matched_roles,
        "matched_skills": matched_skills,
        "experience_matches": experience_matches,
        "location_type": location_type
    })


matched_jobs.sort(
    key=lambda x: x["score"],
    reverse=True
)


print()
print("========================================")
print("              RESULTS")
print("========================================")

print(
    "Total jobs scanned:",
    len(all_jobs)
)

print(
    "India eligible jobs:",
    len(matched_jobs)
)


for number, result in enumerate(
    matched_jobs,
    start=1
):

    job = result["job"]

    print()
    print("----------------------------------------")

    print(
        "#",
        number
    )

    print(
        "Company:",
        job.get("_company")
    )

    print(
        "Job Title:",
        job.get("title")
    )

    print(
        "Location:",
        get_location(job)
    )

    print(
        "Location Type:",
        result["location_type"]
    )

    print(
        "Match Score:",
        str(result["score"]) + "/100"
    )

    print(
        "Matched Roles:",
        ", ".join(result["matched_roles"])
    )

    print(
        "Profile Skills:",
        ", ".join(result["matched_skills"])
        if result["matched_skills"]
        else "None"
    )

    print(
        "Experience Keywords:",
        ", ".join(result["experience_matches"])
        if result["experience_matches"]
        else "None"
    )

    print(
        "URL:",
        job.get("absolute_url")
    )


print()
print("========================================")
print("            SCAN COMPLETED")
print("========================================")