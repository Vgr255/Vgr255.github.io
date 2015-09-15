# tool to automatically generate a file with the character's content

import collections
import importlib
import os

# Settings

BACKGROUND_COLOR = 0xDDDDDD
TABSIZE = 2

# Stop editing here

TAB = " " * TABSIZE

LINE = (TAB * 2) + "<h2><b>{0}:</b> {1}</h2>\n"
FAMILY_SUMMONS_LINE = (TAB * 3) + "<li><i>{0}</i> ({1})</li>\n"

CHAR_REF = "<a href=\"{0}.html\" title={1}>{1}</a>"

ORDER = ("Name", "Element", "Class", "Weapon", "Birth", "Birth location",
         "Death", "Death location", "Letter", "Recruitment order", "S-Team Rank")

TEXTS = ("Summary", "Abilities", "Backstory", "Highlights")

CHARACTERS = {}

SUMMONS = collections.defaultdict(set)

def _get_name(name):
    file = CHARACTERS[name][0]
    new = name.split()
    if len(new) == 1:
        return new[0]
    if file in new: # support for Liakin and possibly others
        return file
    return new[0]

def parse():
    waiting = []
    num = 10
    total = 0

    for file in os.listdir(os.path.join(os.getcwd(), "Characters", "_data")):
        if not file.endswith(".py") or file.startswith("__init__"):
            continue

        module = importlib.import_module("Characters._data." + file[:-3])

        # sort characters by their letter if applicable, then by their S-Team rank, and the rest (Marlene) go last

        if getattr(module, "LETTER", None):
            CHARACTERS[module.NAME] = (module.FILE, ord(module.LETTER.upper()) - 64)
            total += 1

        elif getattr(module, "S_TEAM_RANK", None) is not None:
            waiting.append((module.NAME, module.FILE, int(module.S_TEAM_RANK)))

        else:
            waiting.append((module.NAME, module.FILE, num))
            num += 1

        for summon in getattr(module, "SUMMONS", []):
            SUMMONS[summon].add(module.NAME)

    waiting.sort(key=lambda x: x[2])

    for character, link, rank in waiting:
        total += 1
        CHARACTERS[character] = (link, total)

def generate_characters():
    for file in os.listdir(os.path.join(os.getcwd(), "Characters", "_data")):
        if not file.endswith(".py") or file.startswith("__init__"):
            continue

        module = importlib.import_module("Characters._data." + file[:-3])

        with open(os.path.join(os.getcwd(), "Characters", "{0}.html".format(module.FILE)), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n<! AUTOMATICALLY GENERATED HTML CODE !>\n\n")
            f.write("<meta charset=\"utf-8\" />\n\n<html>\n")
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
                    summoners = sorted(SUMMONS[summon], key=lambda x: 0 if x == module.NAME else CHARACTERS[x][1])
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

            f.write("\n{0}{0}<p><b><a href=\"../index.html\" title=\"Back to Index\">Back to Index</a></b></p>\n\n</html>\n".format(TAB))

if __name__ == "__main__":
    parse()
    generate_characters()
