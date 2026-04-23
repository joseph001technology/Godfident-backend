# app/services/bible_service.py
"""
Static Bible data service.
In production you'd connect to a Bible API (e.g. api.scripture.api.bible)
or load from a full JSON dataset. This provides a rich demo dataset.
"""
from datetime import datetime, date
from typing import List, Optional, Dict
import random

BOOKS_OT = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi"
]

BOOKS_NT = [
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
]

PSALM_23 = [
    (1, "The LORD is my shepherd; I shall not want."),
    (2, "He maketh me to lie down in green pastures: he leadeth me beside the still waters."),
    (3, "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake."),
    (4, "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me."),
    (5, "Thou preparest a table before me in the presence of mine enemies: thou anointest my head with oil; my cup runneth over."),
    (6, "Surely goodness and mercy shall follow me all the days of my life: and I will dwell in the house of the LORD for ever."),
]

JOHN_3 = [
    (1, "There was a man of the Pharisees, named Nicodemus, a ruler of the Jews:"),
    (2, "The same came to Jesus by night, and said unto him, Rabbi, we know that thou art a teacher come from God: for no man can do these miracles that thou doest, except God be with him."),
    (3, "Jesus answered and said unto him, Verily, verily, I say unto thee, Except a man be born again, he cannot see the kingdom of God."),
    (4, "Nicodemus saith unto him, How can a man be born when he is old? can he enter the second time into his mother's womb, and be born?"),
    (5, "Jesus answered, Verily, verily, I say unto thee, Except a man be born of water and of the Spirit, he cannot enter into the kingdom of God."),
    (14, "And as Moses lifted up the serpent in the wilderness, even so must the Son of man be lifted up:"),
    (15, "That whosoever believeth in him should not perish, but have eternal life."),
    (16, "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."),
    (17, "For God sent not his Son into the world to condemn the world; but that the world through him might be saved."),
]

PHILIPPIANS_4 = [
    (4, "Rejoice in the Lord alway: and again I say, Rejoice."),
    (5, "Let your moderation be known unto all men. The Lord is at hand."),
    (6, "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God."),
    (7, "And the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus."),
    (8, "Finally, brethren, whatsoever things are true, whatsoever things are honest, whatsoever things are just, whatsoever things are pure, whatsoever things are lovely, whatsoever things are of good report; if there be any virtue, and if there be any praise, think on these things."),
    (13, "I can do all things through Christ which strengtheneth me."),
    (19, "But my God shall supply all your need according to his riches in glory by Christ Jesus."),
]

ISAIAH_40 = [
    (28, "Hast thou not known? hast thou not heard, that the everlasting God, the LORD, the Creator of the ends of the earth, fainteth not, neither is weary? there is no searching of his understanding."),
    (29, "He giveth power to the faint; and to them that have no might he increaseth strength."),
    (30, "Even the youths shall faint and be weary, and the young men shall utterly fall:"),
    (31, "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."),
]

PROVERBS_3 = [
    (1, "My son, forget not my law; but let thine heart keep my commandments:"),
    (3, "Let not mercy and truth forsake thee: bind them about thy neck; write them upon the table of thine heart:"),
    (5, "Trust in the LORD with all thine heart; and lean not unto thine own understanding."),
    (6, "In all thy ways acknowledge him, and he shall direct thy paths."),
    (7, "Be not wise in thine own eyes: fear the LORD, and depart from evil."),
]

ROMANS_8 = [
    (28, "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."),
    (31, "What shall we then say to these things? If God be for us, who can be against us?"),
    (37, "Nay, in all these things we are more than conquerors through him that loved us."),
    (38, "For I am persuaded, that neither death, nor life, nor angels, nor principalities, nor powers, nor things present, nor things to come,"),
    (39, "Nor height, nor depth, nor any other creature, shall be able to separate us from the love of God, which is in Christ Jesus our Lord."),
]

MATTHEW_6 = [
    (9, "After this manner therefore pray ye: Our Father which art in heaven, Hallowed be thy name."),
    (10, "Thy kingdom come, Thy will be done in earth, as it is in heaven."),
    (11, "Give us this day our daily bread."),
    (12, "And forgive us our debts, as we forgive our debtors."),
    (13, "And lead us not into temptation, but deliver us from evil: For thine is the kingdom, and the power, and the glory, for ever. Amen."),
    (33, "But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you."),
]

BIBLE_DATA: Dict = {
    "Psalms": {
        23: [(n, t) for n, t in PSALM_23],
    },
    "John": {
        3: [(n, t) for n, t in JOHN_3],
    },
    "Philippians": {
        4: [(n, t) for n, t in PHILIPPIANS_4],
    },
    "Isaiah": {
        40: [(n, t) for n, t in ISAIAH_40],
    },
    "Proverbs": {
        3: [(n, t) for n, t in PROVERBS_3],
    },
    "Romans": {
        8: [(n, t) for n, t in ROMANS_8],
    },
    "Matthew": {
        6: [(n, t) for n, t in MATTHEW_6],
    },
}

DAILY_VERSES = [
    {"text": "I can do all things through Christ which strengtheneth me.", "reference": "Philippians 4:13", "book": "Philippians", "chapter": 4, "verse": 13, "theme": "strength"},
    {"text": "The LORD is my shepherd; I shall not want.", "reference": "Psalm 23:1", "book": "Psalms", "chapter": 23, "verse": 1, "theme": "provision"},
    {"text": "Trust in the LORD with all thine heart; and lean not unto thine own understanding.", "reference": "Proverbs 3:5", "book": "Proverbs", "chapter": 3, "verse": 5, "theme": "trust"},
    {"text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.", "reference": "John 3:16", "book": "John", "chapter": 3, "verse": 16, "theme": "love"},
    {"text": "Be strong and courageous. Do not be afraid; do not be discouraged, for the LORD your God will be with you wherever you go.", "reference": "Joshua 1:9", "book": "Joshua", "chapter": 1, "verse": 9, "theme": "courage"},
    {"text": "Come unto me, all ye that labour and are heavy laden, and I will give you rest.", "reference": "Matthew 11:28", "book": "Matthew", "chapter": 11, "verse": 28, "theme": "rest"},
    {"text": "Casting all your care upon him; for he careth for you.", "reference": "1 Peter 5:7", "book": "1 Peter", "chapter": 5, "verse": 7, "theme": "peace"},
    {"text": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles.", "reference": "Isaiah 40:31", "book": "Isaiah", "chapter": 40, "verse": 31, "theme": "hope"},
    {"text": "And we know that all things work together for good to them that love God.", "reference": "Romans 8:28", "book": "Romans", "chapter": 8, "verse": 28, "theme": "purpose"},
    {"text": "But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you.", "reference": "Matthew 6:33", "book": "Matthew", "chapter": 6, "verse": 33, "theme": "priority"},
    {"text": "If God be for us, who can be against us?", "reference": "Romans 8:31", "book": "Romans", "chapter": 8, "verse": 31, "theme": "victory"},
    {"text": "The peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus.", "reference": "Philippians 4:7", "book": "Philippians", "chapter": 4, "verse": 7, "theme": "peace"},
    {"text": "I will never leave thee, nor forsake thee.", "reference": "Hebrews 13:5", "book": "Hebrews", "chapter": 13, "verse": 5, "theme": "presence"},
    {"text": "Rejoice in the Lord alway: and again I say, Rejoice.", "reference": "Philippians 4:4", "book": "Philippians", "chapter": 4, "verse": 4, "theme": "joy"},
    {"text": "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end.", "reference": "Jeremiah 29:11", "book": "Jeremiah", "chapter": 29, "verse": 11, "theme": "hope"},
]


def get_verse_of_day() -> dict:
    """Rotate verse based on day of year for consistency."""
    day_of_year = datetime.now().timetuple().tm_yday
    return DAILY_VERSES[day_of_year % len(DAILY_VERSES)]


def get_chapter(book: str, chapter: int) -> Optional[List[dict]]:
    book_data = BIBLE_DATA.get(book)
    if not book_data:
        return None
    chapter_data = book_data.get(chapter)
    if not chapter_data:
        return None
    testament = "NT" if book in BOOKS_NT else "OT"
    return [
        {"book": book, "chapter": chapter, "verse": v, "text": t, "testament": testament}
        for v, t in chapter_data
    ]


def search_verses(query: str, limit: int = 20) -> List[dict]:
    results = []
    q = query.lower()
    for book, chapters in BIBLE_DATA.items():
        testament = "NT" if book in BOOKS_NT else "OT"
        for chapter_num, verses in chapters.items():
            for verse_num, text in verses:
                if q in text.lower() or q in book.lower():
                    results.append({
                        "book": book, "chapter": chapter_num,
                        "verse": verse_num, "text": text, "testament": testament
                    })
    return results[:limit]


def get_books_list() -> dict:
    return {"OT": BOOKS_OT, "NT": BOOKS_NT}


def get_random_inspirational_verse() -> dict:
    return random.choice(DAILY_VERSES)
