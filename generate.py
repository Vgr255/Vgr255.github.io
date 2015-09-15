# tool to automatically generate a file with the character's content

import collections
import importlib
import os

# Settings

BACKGROUND_COLOR = 0xDDDDDD
TABSIZE = 2

HEADER = "<!DOCTYPE html>\n<!-- AUTOMATICALLY GENERATED HTML CODE -->\n\n<meta charset=\"utf-8\" />\n\n<html>\n"

LINK = "https://github.com/Vgr255/Vgr255.github.io"

# Stop editing here

TAB = " " * TABSIZE

LINE = (TAB * 2) + "<h2><b>{0}:</b> {1}</h2>\n"
FAMILY_SUMMONS_LINE = (TAB * 3) + "<li><i>{0}</i> ({1})</li>\n"
CHARACTER_LINE = (TAB * 4) + "<li><b>{0}<a href=\"{1}.html\" title=\"{2}\">{2}</a></b></li>\n"

PARAGRAPH = "{0}{0}{0}</ul>\n{0}{0}</p>\n\n{0}{0}<p>\n{0}{0}{0}<h2>{1}</h2>\n{0}{0}{0}<ul>\n"

CHAR_REF = "<a href=\"{0}.html\" title=\"{1}\">{1}</a>"

ORDER = ("Name", "Element", "Class", "Weapon", "Birth", "Birth location",
         "Death", "Death location", "Letter", "Recruitment order", "S-Team Rank")

TEXTS = ("Summary", "Abilities", "Backstory", "Highlights")

CHARACTERS = {}

SUMANSIANS = set()

SUMMONS = collections.defaultdict(set)

def _get_name(name):
    file = CHARACTERS[name][0]
    new = name.split()
    if len(new) == 1:
        return new[0]
    if file in new: # support for Liakin and possibly others
        return file
    return new[0]

def get_sumansians():
    new = []
    rest = set()
    for sumansian in (x for x in CHARACTERS if getattr(CHARACTERS[x][1], "SUMANSIAN", None)):
        if sumansian in new or sumansian in rest:
            continue
        new.append(sumansian)
        for name, twin in SUMANSIANS:
            if name is None:
                rest.add(twin)
            elif twin is None:
                rest.add(name)
            elif sumansian == name:
                new.append(twin)
            elif sumansian == twin:
                new.append(name)

    pairs = list(zip(new[::2], new[1::2]))

    final = []
    num = 0

    for c1, c2 in pairs:
        m1 = CHARACTERS[c1][1]
        m2 = CHARACTERS[c2][1]

        v1 = getattr(m1, "S_TEAM_RANK", ord(getattr(m1, "LETTER", "_")))
        v2 = getattr(m2, "S_TEAM_RANK", ord(getattr(m2, "LETTER", "_")))

        if v1 < v2:
            final.append(((c1, v1), (c2, v2)))
        else:
            final.append(((c2, v2), (c1, v1)))

    final.sort(key=lambda x: x[0][1])

    ret = []

    for tup in zip((x[0][0] for x in final), (x[1][0] for x in final)):
        ret.extend(tup)

    ret.extend(rest)

    return ret

def parse_characters():
    waiting = []
    num = 10
    total = 0

    for file in os.listdir(os.path.join(os.getcwd(), "Characters", "_data")):
        if not file.endswith(".py") or file.startswith("__init__"):
            continue

        module = importlib.import_module("Characters._data." + file[:-3])

        # sort characters by their letter if applicable, then by their S-Team rank, and the rest (Marlene) go last

        if getattr(module, "LETTER", None):
            CHARACTERS[module.NAME] = (module.FILE, module, ord(module.LETTER.upper()) - 64)
            total += 1

        elif getattr(module, "S_TEAM_RANK", None) is not None:
            waiting.append((module, int(module.S_TEAM_RANK)))

        else:
            waiting.append((module, num))
            num += 1

        if getattr(module, "SUMANSIAN", None):
            SUMANSIANS.add(frozenset({module.NAME, getattr(module, "SUMANSIAN_TWIN", None)}))

        for summon in getattr(module, "SUMMONS", []):
            SUMMONS[summon].add(module.NAME)

    waiting.sort(key=lambda x: x[1])

    for module, rank in waiting:
        total += 1
        CHARACTERS[module.NAME] = (module.FILE, module, total)

def generate_characters():
    for file in os.listdir(os.path.join(os.getcwd(), "Characters", "_data")):
        if not file.endswith(".py") or file.startswith("__init__"):
            continue

        module = importlib.import_module("Characters._data." + file[:-3])

        with open(os.path.join(os.getcwd(), "Characters", "{0}.html".format(module.FILE)), "w", encoding="utf-8") as f:
            f.write(HEADER)
            f.write("{0}<head>\n{0}{0}<title>{1}</title>\n{0}</head>\n\n".format(TAB, module.NAME))
            f.write("{0}<body style=\"background-color:#{1:06x};\">\n".format(TAB, BACKGROUND_COLOR))
            for item in ORDER:
                value = getattr(module, item.replace("-", "_").replace(" ", "_").upper(), None)
                isstr = isinstance(value, str) and not value.isdigit()
                f.write(LINE.format(item, "{0}{1}{2}".format("<i>" if isstr else "", value, "</i>" if isstr else "")))

            great_four = " [One of the Great Four]" if getattr(module, "GREAT_FOUR", False) else ""
            f.write(LINE.format("Sumansian", ("Yes" if getattr(module, "SUMANSIAN", False) else "No") + great_four))

            value = twin = getattr(module, "SUMANSIAN_TWIN", None)
            isstr = isinstance(value, str) and value != "Unknown"
            if value in CHARACTERS:
                value = CHAR_REF.format(CHARACTERS[value][0], value)
            f.write(LINE.format("Sumansian twin", "{0}{1}{2}".format("<i>" if isstr else "", value, "</i>" if isstr else "")))

            if twin and twin not in getattr(module, "FAMILY", ()): # corner case of Jeremy/Amelia
                module.FAMILY = ((value, "Sumansian twin"),) + getattr(module, "FAMILY", ())

            if getattr(module, "FAMILY", None):
                f.write("\n{0}{0}<h2><b>Family:</b></h2>\n{0}{0}<ul>\n".format(TAB))
                for member, relation in module.FAMILY:
                    if member in CHARACTERS:
                        member = CHAR_REF.format(CHARACTERS[member][0], member)
                    f.write(FAMILY_SUMMONS_LINE.format(member, relation))
                f.write("{0}{0}</ul>\n".format(TAB))
            else: # poor character doesn't even have any family :(
                f.write("\n{0}{0}<h2><b>Family:</b> Unknown</h2>\n".format(TAB))

            if getattr(module, "SUMMONS", None):
                f.write("\n{0}{0}<h2><b>Summons:</b></h2>\n{0}{0}<ul>\n".format(TAB))
                for summon in module.SUMMONS:
                    summoners = sorted(SUMMONS[summon], key=lambda x: 0 if x == module.NAME else CHARACTERS[x][2])
                    new = []
                    for i, summoner in enumerate(summoners):
                        if i == 0:
                            new.append(_get_name(summoner))
                        else:
                            if summoner in CHARACTERS:
                                summoner = CHAR_REF.format(CHARACTERS[summoner][0], summoner)
                            new.append(summoner)
                    f.write(FAMILY_SUMMONS_LINE.format(summon, ", ".join(new)))
                f.write("{0}{0}</ul>\n".format(TAB))
            else:
                f.write("\n{0}{0}<h2><b>Summons:</b> None</h2>\n".format(TAB))

            for item in TEXTS:
                if getattr(module, item.upper(), None):
                    f.write("\n{0}{0}<h2><b>{1}:</b></h2>\n{0}{0}{2}\n".format(TAB, item, getattr(module, item.upper())))
                else:
                    f.write("\n{0}{0}<h2><b>{1}:</b> None</h2>\n".format(TAB, item))

            f.write("\n{0}{0}<p><b>{1}</b></p>\n".format(TAB, CHAR_REF.format("index", "Back to Character Index")))
            f.write("{0}{0}<p><b>{1}</b></p>\n\n{0}</body>\n</html>\n".format(TAB, CHAR_REF.format("../index", "Back to Index")))

def generate_character_index():
    with open(os.path.join(os.getcwd(), "Characters", "index.html"), "w", encoding="utf-8") as f:
        f.write(HEADER)
        f.write("{0}<head>\n{0}{0}<title>Characters Index</title>\n{0}</head>\n\n".format(TAB))
        f.write("{0}<body style=\"background-color:#{1:06x};\">\n".format(TAB, BACKGROUND_COLOR))
        f.write("{0}{0}<h1>Characters</h1>\n{0}{0}<p>\n{0}{0}{0}<h2>\"Them\"</h2>\n{0}{0}{0}<ul>\n".format(TAB))

        them = [x for x in CHARACTERS if getattr(CHARACTERS[x][1], "LETTER", None)]
        them.sort(key=lambda x: CHARACTERS[x][2])

        for c in them:
            f.write(CHARACTER_LINE.format("{0}: ".format(CHARACTERS[c][1].LETTER), CHARACTERS[c][0], c))

        f.write(PARAGRAPH.format(TAB, "S-Team"))

        s_team = [x for x in CHARACTERS if getattr(CHARACTERS[x][1], "S_TEAM_RANK", None) is not None]
        s_team.sort(key=lambda x: CHARACTERS[x][1].S_TEAM_RANK)
        s_team.append(s_team.pop(0)) # Handle Arya

        for c in s_team:
            f.write(CHARACTER_LINE.format("{0}: ".format(CHARACTERS[c][1].S_TEAM_RANK), CHARACTERS[c][0], c))

        f.write(PARAGRAPH.format(TAB, "The Great Four"))

        great_four = [x for x in CHARACTERS if getattr(CHARACTERS[x][1], "GREAT_FOUR", None)]
        great_four.sort(key=lambda x: CHARACTERS[x][2])

        for c in great_four:
            f.write(CHARACTER_LINE.format("", CHARACTERS[c][0], c))

        f.write(PARAGRAPH.format(TAB, "Sumansians"))

        sumansians = get_sumansians()

        for c in sumansians:
            f.write(CHARACTER_LINE.format("", CHARACTERS[c][0], c))

        other = [x for x in CHARACTERS if x not in them + s_team + great_four + sumansians]
        other.sort(key=lambda x: CHARACTERS[x][2])

        if other:
            f.write(PARAGRAPH.format(TAB, "Other"))

            for c in other:
                f.write(CHARACTER_LINE.format("", CHARACTERS[c][0], c))

        f.write("{0}{0}{0}</ul>\n{0}{0}</p>\n\n{0}{0}<p>".format(TAB))
        f.write(CHAR_REF.format("../index", "Back to Index"))
        f.write("</p>\n{0}{0}<p>".format(TAB))
        f.write(CHAR_REF.format(LINK, "Source Code on GitHub"))
        f.write("</p>\n\n{0}</body>\n</html>\n".format(TAB))

def generate_index():
    with open(os.path.join(os.getcwd(), "index.html"), "w", encoding="utf-8") as f:
        f.write(HEADER)
        f.write("{0}<head>\n{0}{0}<title>Vgr's Personal Website</title>\n{0}</head>\n\n".format(TAB))
        f.write("{0}<body style=\"background-color:#{1:06x};\">\n".format(TAB, BACKGROUND_COLOR))

        folders = [os.getcwd()]
        data = []

        while folders:
            folder = folders.pop(0)

            for file in os.listdir(folder):
                if os.path.isdir(os.path.join(folder, file)) and not file.startswith((".", "_")):
                    folders.append(os.path.join(folder, file))
                    data.append(os.path.join(folder, file))

        for folder in data:
            f.write("{0}{0}<h1>{1}</h1>\n".format(TAB, CHAR_REF.format("/".join((folder[len(os.getcwd())+1:].replace(os.sep, "/"), "index")), os.path.split(folder)[1])))

        f.write("\n{0}{0}<p><a href=\"{1}\" title=\"{2}\">{2}</a></p>\n{0}</body>\n</html>\n".format(TAB, LINK, "Source Code on GitHub"))

if __name__ == "__main__":
    parse_characters()
    generate_characters()
    generate_character_index()
    generate_index()
