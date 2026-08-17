import re
from html import unescape

from workers import fetch


# ============================================================
# COMPANIES
# ============================================================

COMPANIES = {
    "Stripe": "stripe",
    "Coinbase": "coinbase",
    "NICE": "nice",
    "Robinhood": "robinhood",
}


# ============================================================
# INDIA LOCATIONS
# ============================================================

INDIA_LOCATIONS = {
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
}


INDIA_REMOTE_PHRASES = {
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
}


# ============================================================
# ROLE KEYWORDS
# ============================================================

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


# ============================================================
# PROFILE SKILLS
# ============================================================

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


# ============================================================
# EXCLUDED TITLES
# ============================================================

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


# ============================================================
# EXPERIENCE KEYWORDS
# ============================================================

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


# ============================================================
# LIMITS
# ============================================================

# Maximum number of promising jobs for which we download
# the full description.
MAX_DETAIL_JOBS_PER_COMPANY = 30

# Maximum final results returned to Worker.
MAX_FINAL_RESULTS = 20


# ============================================================
# HELPERS
# ============================================================

def clean_html(text):
    text = re.sub(
        r"<[^>]+>",
        " ",
        text or "",
    )

    text = unescape(text)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "").lower(),
    ).strip()


def get_location(job):
    location = job.get(
        "location",
        {},
    )

    if isinstance(location, dict):
        return str(
            location.get(
                "name",
                "",
            )
        )

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
    if location_type == "INDIA_REMOTE":
        return 20

    if location_type == "INDIA":
        return 15

    return 0


def title_is_excluded(title_lower):
    for keyword in EXCLUDED_TITLE_KEYWORDS:
        if keyword in title_lower:
            return True

    return False


def find_roles(title, description=""):
    title_lower = normalize(title)
    description_lower = normalize(description)

    matched_roles = []

    # Title gets priority.
    for role, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title_lower:

                if role not in matched_roles:
                    matched_roles.append(role)

                break

    # If title has no direct role match, allow description match
    # only for stronger broad categories.
    if not matched_roles and description_lower:

        for role, keywords in ROLE_KEYWORDS.items():

            for keyword in keywords:

                if keyword in description_lower:

                    if role not in matched_roles:
                        matched_roles.append(role)

                    break

    return matched_roles


def title_role_candidates(title):
    title_lower = normalize(title)

    if title_is_excluded(title_lower):
        return []

    matched_roles = []

    for role, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title_lower:

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

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    score += location_score(
        location_type
    )

    # --------------------------------------------------------
    # Role relevance
    # --------------------------------------------------------

    if matched_roles:
        score += min(
            len(matched_roles) * 20,
            40,
        )

    # --------------------------------------------------------
    # Strong title relevance
    # --------------------------------------------------------

    title_role_hits = 0

    for role, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title_lower:
                title_role_hits += 1
                break

    score += min(
        title_role_hits * 10,
        30,
    )

    # --------------------------------------------------------
    # Profile skills
    # --------------------------------------------------------

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

    score = min(
        score,
        100,
    )

    return score, skill_matches


def find_experience_matches(description):
    description_lower = normalize(
        description
    )

    matches = []

    for keyword in EXPERIENCE_KEYWORDS:

        if keyword in description_lower:

            if keyword not in matches:
                matches.append(keyword)

    return matches


# ============================================================
# GREENHOUSE JOB LIST
# ============================================================

async def fetch_greenhouse_job_list(
    company_name,
    board_token,
):
    """
    Fetch lightweight job listing.

    IMPORTANT:
    We intentionally do NOT use content=true here.
    This prevents downloading thousands of large descriptions
    during the first stage of the scan.
    """

    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        + board_token
        + "/jobs"
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

        jobs = data.get(
            "jobs",
            [],
        )

        for job in jobs:
            job["_company"] = company_name

        print(
            "Jobs listed:",
            company_name,
            len(jobs),
        )

        return jobs

    except Exception as error:

        print(
            "List error:",
            company_name,
            "|",
            repr(error),
        )

        return []


# ============================================================
# INDIVIDUAL JOB DETAILS
# ============================================================

async def fetch_job_details(
    company_name,
    board_token,
    job_id,
):
    """
    Fetch full description only after the job has passed
    the lightweight title/location filter.
    """

    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        + board_token
        + "/jobs/"
        + str(job_id)
        + "?content=true"
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
                "Detail skipped:",
                company_name,
                job_id,
                "| HTTP",
                response.status,
            )

            return None

        job = await response.json()

        job["_company"] = company_name

        return job

    except Exception as error:

        print(
            "Detail error:",
            company_name,
            job_id,
            "|",
            repr(error),
        )

        return None


# ============================================================
# SCAN
# ============================================================

async def scan_jobs():

    print()
    print("========================================")
    print("       AML / KYC CLOUD JOB HUNTER")
    print("========================================")

    all_candidates = []

    # ========================================================
    # STAGE 1
    # Lightweight company scan
    # ========================================================

    for company_name, board_token in COMPANIES.items():

        print()
        print(
            "Scanning:",
            company_name,
        )

        jobs = await fetch_greenhouse_job_list(
            company_name,
            board_token,
        )

        for job in jobs:

            title = job.get(
                "title",
                "",
            )

            location = get_location(
                job
            )

            title_lower = normalize(
                title
            )

            location_type = classify_location(
                location
            )

            if location_type not in (
                "INDIA",
                "INDIA_REMOTE",
            ):
                continue

            if title_is_excluded(
                title_lower
            ):
                continue

            matched_roles = title_role_candidates(
                title
            )

            if not matched_roles:
                continue

            all_candidates.append(
                {
                    "job": job,
                    "company_name": company_name,
                    "board_token": board_token,
                    "matched_roles": matched_roles,
                }
            )

    print()
    print("========================================")
    print("       LIGHTWEIGHT FILTER RESULTS")
    print("========================================")

    print(
        "India role candidates:",
        len(all_candidates),
    )

    if not all_candidates:
        print(
            "No India AML/KYC candidates found."
        )

        return []

    # ========================================================
    # Sort candidates before expensive detail requests
    # ========================================================

    all_candidates.sort(
        key=lambda item: (
            len(
                item["matched_roles"]
            ),
            item["job"].get(
                "title",
                "",
            ),
        ),
        reverse=True,
    )

    # Limit expensive detail requests globally.
    detail_candidates = all_candidates[
        :MAX_DETAIL_JOBS_PER_COMPANY * len(COMPANIES)
    ]

    print(
        "Detailed jobs selected:",
        len(detail_candidates),
    )

    # ========================================================
    # STAGE 2
    # Fetch descriptions only for shortlisted jobs
    # ========================================================

    matched_jobs = []

    detail_count = 0

    for candidate in detail_candidates:

        job = candidate["job"]

        company_name = candidate[
            "company_name"
        ]

        board_token = candidate[
            "board_token"
        ]

        job_id = job.get(
            "id"
        )

        if job_id is None:
            continue

        detail_count += 1

        print(
            "Fetching details:",
            company_name,
            job_id,
        )

        detailed_job = await fetch_job_details(
            company_name,
            board_token,
            job_id,
        )

        if not detailed_job:
            continue

        title = detailed_job.get(
            "title",
            "",
        )

        content = detailed_job.get(
            "content",
            "",
        )

        location = get_location(
            detailed_job
        )

        description = clean_html(
            content
        )

        location_type = classify_location(
            location
        )

        if location_type not in (
            "INDIA",
            "INDIA_REMOTE",
        ):
            continue

        matched_roles = find_roles(
            title,
            description,
        )

        if not matched_roles:
            continue

        score, matched_skills = calculate_score(
            title,
            description,
            location_type,
            matched_roles,
        )

        if score < 50:
            continue

        experience_matches = find_experience_matches(
            description
        )

        matched_jobs.append(
            {
                "job": detailed_job,
                "score": score,
                "matched_roles": matched_roles,
                "matched_skills": matched_skills,
                "experience_matches": experience_matches,
                "location_type": location_type,
            }
        )

    # ========================================================
    # FINAL SORT
    # ========================================================

    matched_jobs.sort(
        key=lambda item: item.get(
            "score",
            0,
        ),
        reverse=True,
    )

    matched_jobs = matched_jobs[
        :MAX_FINAL_RESULTS
    ]

    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("========================================")
    print("              RESULTS")
    print("========================================")

    print(
        "India role candidates:",
        len(all_candidates),
    )

    print(
        "Detailed jobs fetched:",
        detail_count,
    )

    print(
        "Qualified jobs:",
        len(matched_jobs),
    )

    for number, result in enumerate(
        matched_jobs,
        start=1,
    ):

        job = result[
            "job"
        ]

        print()
        print("----------------------------------------")

        print(
            "#",
            number,
        )

        print(
            "Company:",
            job.get(
                "_company"
            ),
        )

        print(
            "Job Title:",
            job.get(
                "title"
            ),
        )

        print(
            "Location:",
            get_location(
                job
            ),
        )

        print(
            "Match Score:",
            str(
                result["score"]
            )
            + "/100",
        )

        print(
            "Matched Roles:",
            ", ".join(
                result[
                    "matched_roles"
                ]
            ),
        )

        print(
            "Profile Skills:",
            ", ".join(
                result[
                    "matched_skills"
                ]
            )
            if result[
                "matched_skills"
            ]
            else "None",
        )

        print(
            "Experience:",
            ", ".join(
                result[
                    "experience_matches"
                ]
            )
            if result[
                "experience_matches"
            ]
            else "None",
        )

        print(
            "URL:",
            job.get(
                "absolute_url"
            ),
        )

    print()
    print("========================================")
    print("          CLOUD SCAN COMPLETED")
    print("========================================")

    return matched_jobs