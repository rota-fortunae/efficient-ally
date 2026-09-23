"""Look up the grade of each requested student (None if they aren't on the roster).

Pattern: nested search by key -> dict.
"""

ROSTER = [("ana", 91), ("ben", 78), ("cho", 85)]
EXAMPLES = [(ROSTER, ["cho", "ana", "dev"]), ([], ["x"])]


def slow(roster: list[tuple], requests: list[str]):
    # expect: O(len(requests) * len(roster))
    grades = []
    for name in requests:
        grade = None
        for student, score in roster:
            if student == name:
                grade = score
                break
        grades.append(grade)
    return grades


def fast(roster: list[tuple], requests: list[str]):
    # expect: O(len(requests) + len(roster))
    grade_of = {}
    for student, score in roster:
        grade_of.setdefault(student, score)
    return [grade_of.get(name) for name in requests]
