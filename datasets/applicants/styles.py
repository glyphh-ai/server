"""The knobs that vary how applications read and look, so no one style or format stands for a class."""

from itertools import product

FIRST: tuple[str, ...] = (
    "Maria",
    "James",
    "Aisha",
    "Wei",
    "Carlos",
    "Priya",
    "Daniel",
    "Fatima",
    "Tomasz",
    "Grace",
    "Kwame",
    "Elena",
    "Mohammed",
    "Hannah",
    "Diego",
    "Mei",
    "Olumide",
    "Sarah",
    "Raj",
    "Lucia",
    "Brandon",
    "Ngozi",
    "Ivan",
    "Keisha",
    "Hiroshi",
    "Rosa",
    "Tyler",
    "Amara",
    "Sven",
    "Leila",
    "Marcus",
    "Yuki",
    "Patrick",
    "Zainab",
    "Andre",
    "Ingrid",
    "Luis",
    "Chloe",
    "Dmitri",
    "Tanya",
    "Samuel",
    "Anh",
    "Rebecca",
    "Omar",
    "Jasmine",
    "Kevin",
    "Esther",
    "Mateo",
)
LAST: tuple[str, ...] = (
    "Garcia",
    "Okafor",
    "Nguyen",
    "Smith",
    "Kowalski",
    "Patel",
    "Johnson",
    "Haddad",
    "Kim",
    "Brown",
    "Mensah",
    "Rossi",
    "Williams",
    "Ivanova",
    "Lopez",
    "Chen",
    "Adeyemi",
    "Murphy",
    "Sharma",
    "Fernandez",
    "Miller",
    "Eze",
    "Petrov",
    "Davis",
    "Tanaka",
    "Morales",
    "Anderson",
    "Abiodun",
    "Larsen",
    "Rahimi",
    "Thompson",
    "Sato",
    "O'Brien",
    "Hussain",
    "Baptiste",
    "Johansson",
    "Ramirez",
    "Dubois",
    "Volkov",
    "Walker",
    "Yilmaz",
)

# How the person writes on their own, with no help: the draft the some/mostly applicants start from.
VOICES: tuple[str, ...] = (
    "terse and plain; short fragments, few adjectives, a couple of typos",
    "chatty and warm; long run-on sentences, exclamation marks, mentions family or hometown",
    "old-school formal; 'To Whom It May Concern', 'References available upon request', a bit stiff",
    "English is a second language; small grammar slips (articles, tense), clear and sincere",
    "nervous new entrant; over-explains, apologises for gaps, lists coursework and part-time jobs",
    "blunt veteran of the trade; numbers and equipment names, no fluff, uneven capitalisation",
    "casual texter; lowercase in places, abbreviations (w/, mgmt, yrs), inconsistent bullet styles",
    "proud and a little boastful; strong claims without polish, repeats 'I' a lot",
    "careful but uneven; good content, mixed tenses, a misspelled company name, one duplicated bullet",
    "minimalist; the resume is mostly a list of jobs and dates, the cover letter is three sentences",
    "story-teller; starts the cover letter with an anecdote from work, rambles a little",
    "rushed; copy-paste leftovers (wrong date or a stray placeholder), missing periods",
)

# How strongly the AI-written text shows it (mostly and fully).
TELLS: tuple[str, ...] = (
    "heavy: the stock AI cover-letter voice; 'I am thrilled to apply', 'proven track record', 'leverage', "
    "'spearheaded', 'passionate about', em dashes, lists of three, a 'Moreover' or 'Furthermore'",
    "moderate: polished and corporate, consistent parallel bullets with metrics on nearly every line, "
    "a confident summary paragraph, tidy and symmetrical",
    "subtle: told to sound natural and avoid cliches; still very even, grammatical and well structured, "
    "with no slips and smooth transitions",
    "templated: reads like a filled-in template; bracket-perfect structure, generic achievements, "
    "a skills section of buzzwords, the company name repeated in every paragraph",
)

# What the light AI edit touched (some): one part polished, the rest left as the person wrote it.
EDITS: tuple[str, ...] = (
    "fix grammar and spelling in the cover letter only; change nothing else",
    "rewrite only the resume summary in a polished professional voice; leave every other part word for word",
    "rewrite only the cover letter's opening and closing paragraphs; keep the middle and the resume as is",
    "tighten and polish the bullets of the most recent job only; leave every other part word for word",
    "rewrite only the email body to sound professional; leave the cover letter and resume as is",
)

FONTS: tuple[str, ...] = ("Calibri", "Arial", "Georgia", "Garamond", "Times New Roman", "Courier New")
PDF_FONT: dict[str, str] = {
    "Calibri": "Helvetica",
    "Arial": "Helvetica",
    "Georgia": "Times-Roman",
    "Garamond": "Times-Roman",
    "Times New Roman": "Times-Roman",
    "Courier New": "Courier",
}
PDF_BOLD: dict[str, str] = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold", "Courier": "Courier-Bold"}
LAYOUT_NAMES: tuple[str, ...] = ("classic", "modern", "compact", "plain")
LAYOUTS: tuple[tuple[str, str], ...] = tuple(product(LAYOUT_NAMES, FONTS))
