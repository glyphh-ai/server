"""The role postings the applicants apply to: ten fields, each with the must-haves the fit label is built from."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    key: str
    title: str
    company: str
    city: str
    years: tuple[int, int]  # the experience the posting asks for
    must: tuple[str, ...]  # what a strong applicant has, all of it
    nice: tuple[str, ...]
    adjacent: str  # the near-miss background a borderline applicant comes from
    duties: str

    def posting(self) -> str:
        return (
            f"{self.title} at {self.company} ({self.city}). {self.duties} "
            f"Requires {self.years[0]}+ years of experience and: {', '.join(self.must)}. "
            f"Nice to have: {', '.join(self.nice)}."
        )


ROLES: tuple[Role, ...] = (
    Role(
        "backend-engineer",
        "Senior Backend Engineer",
        "Ledgerline",
        "Austin, TX",
        (5, 12),
        ("Python", "PostgreSQL", "REST API design", "cloud deployment (AWS or GCP)", "code review and mentoring"),
        ("Kubernetes", "payments systems", "event queues (Kafka or SQS)", "observability tooling"),
        "a frontend or QA engineer who has done some backend work",
        "You will build and run the services behind our invoicing product and help grow a team of six.",
    ),
    Role(
        "icu-nurse",
        "ICU Registered Nurse",
        "St. Brigid Medical Center",
        "Columbus, OH",
        (2, 15),
        ("active RN license", "BLS and ACLS", "critical care experience", "ventilator management", "EHR charting"),
        ("CCRN certification", "CRRT", "charge nurse experience", "preceptor experience"),
        "a med-surg or telemetry nurse with no ICU time",
        "Twelve-hour shifts caring for two critically ill patients in a 24-bed mixed ICU.",
    ),
    Role(
        "marketing-manager",
        "B2B Marketing Manager",
        "Fernwork",
        "Denver, CO",
        (4, 10),
        (
            "B2B demand generation",
            "marketing automation (HubSpot or Marketo)",
            "campaign budget ownership",
            "content strategy",
            "pipeline reporting",
        ),
        ("SaaS experience", "ABM programs", "SQL or BI dashboards", "managing agencies"),
        "a B2C social media or brand coordinator",
        "Own the pipeline targets for our mid-market segment and run a small team plus agencies.",
    ),
    Role(
        "financial-analyst",
        "FP&A Financial Analyst",
        "Harlow Freight",
        "Charlotte, NC",
        (2, 6),
        (
            "financial modeling in Excel",
            "budgeting and forecasting",
            "variance analysis",
            "month-end close support",
            "presenting to managers",
        ),
        ("CPA or CFA progress", "NetSuite or SAP", "Power BI or Tableau", "logistics industry"),
        "a staff accountant or bookkeeper who has not done forecasting",
        "Build the monthly forecast for three business units and explain the numbers to their leaders.",
    ),
    Role(
        "teacher",
        "4th Grade Teacher",
        "Maple Hollow Elementary",
        "Sacramento, CA",
        (1, 20),
        (
            "state teaching credential",
            "elementary classroom experience",
            "lesson planning to state standards",
            "classroom management",
            "parent communication",
        ),
        ("bilingual (Spanish)", "special education experience", "reading intervention", "STEM club leadership"),
        "a substitute teacher or tutor without a credential",
        "Lead a class of 26 fourth graders and plan with a grade-level team of three.",
    ),
    Role(
        "warehouse-supervisor",
        "Warehouse Operations Supervisor",
        "Northgate Distribution",
        "Joliet, IL",
        (3, 15),
        (
            "supervising hourly teams",
            "WMS software",
            "OSHA safety programs",
            "inventory accuracy and cycle counts",
            "shift scheduling",
        ),
        ("forklift certification", "lean or six sigma", "union environment", "bilingual (Spanish)"),
        "a senior warehouse associate or team lead who has not supervised a shift",
        "Run the night shift of 40 associates across receiving, picking and shipping.",
    ),
    Role(
        "ux-designer",
        "Product (UX) Designer",
        "Tidepool Health",
        "Remote (US)",
        (3, 8),
        (
            "a portfolio of shipped product work",
            "Figma",
            "user research",
            "interaction design",
            "working with engineers",
        ),
        ("healthcare products", "design systems", "accessibility (WCAG)", "prototyping in code"),
        "a graphic or visual designer moving into product work",
        "Design the patient app end to end with one PM and five engineers.",
    ),
    Role(
        "paralegal",
        "Litigation Paralegal",
        "Okafor & Pratt LLP",
        "Philadelphia, PA",
        (2, 10),
        (
            "litigation support",
            "e-discovery tools (Relativity)",
            "drafting pleadings and discovery",
            "court filing procedures",
            "managing case calendars",
        ),
        ("paralegal certificate", "trial preparation", "medical records review", "Spanish"),
        "a legal secretary or receptionist at a small firm",
        "Support two partners in commercial litigation from intake through trial.",
    ),
    Role(
        "sous-chef",
        "Sous Chef",
        "Juniper & Ash",
        "Portland, OR",
        (3, 12),
        (
            "line cooking in a high-volume kitchen",
            "running a station and the pass",
            "food safety certification",
            "inventory and ordering",
            "training cooks",
        ),
        ("menu development", "butchery", "farm-to-table sourcing", "food cost control"),
        "a line cook who has not run a kitchen",
        "Run service four nights a week in a 120-cover restaurant and lead a crew of eight.",
    ),
    Role(
        "hvac-tech",
        "Commercial HVAC Technician",
        "Brightline Mechanical",
        "Phoenix, AZ",
        (3, 20),
        (
            "EPA 608 certification",
            "commercial rooftop units",
            "troubleshooting controls and electrical",
            "preventive maintenance",
            "valid driver's license",
        ),
        ("chillers", "building automation systems", "NATE certification", "customer-facing service calls"),
        "a residential HVAC installer with little commercial work",
        "Service and repair commercial systems across the Phoenix metro from a company truck.",
    ),
)

BY_KEY: dict[str, Role] = {r.key: r for r in ROLES}
