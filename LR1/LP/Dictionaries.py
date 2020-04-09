# -*- coding: utf-8 -*-
from abc import ABC
import os
import re
from LP.Consts import *

# словари лингвистического процессора
DICT_FOLDER = os.path.join('data', 'dictionaries')

# Словарь квазифлексий
FLEXIES_DICT = 'Flexies.dct'
# Словарь характеристик
CHARACTERS_DICT = "Characters.dct"
# Словарь понятий
ENTITIES_DICT = "Entities.dct"
# Словарь глаголов
VERBS_DICT = "Verbs.dct"
# Словарь предикатов (моделей управления)
PREDICATES_DICT = "Predicates.dct"
# Словарь сложных лексем
GLUED_WORDS_DICT = 'GluedWords.dct'
# Словарь готовых словоформ
NONINFLECTED_WORDS_DICT = 'NoninflectedWords.dct'
# Словарь синонимов: (номер, каноническая форма, {синоним})
SYNONYMS_DICT = 'Synonyms.dct'
# Словарь параметров: (атом пролога, каноническая форма)
PARAMETERS_DICT = 'Parameters.dct'
# Словарь единиц измерения: (атом пролога, обозначение, каноническая форма)
UNITS_DICT = 'Units.dct'
# Словарь семантических категорий
SEMANTIC_CATEGORIES_DICT = 'SemCat.dct'

# Корпус задач
TASK_CORPUS_FILE = 'TaskCorpus.txt'

"""
        Структура модели управления: [ (actant_type, [(preposition, case_type)], [semantic_category]]
        Пример в словарной статье предиката:
        ( ( O ( РП ) ( ЗАБ ) ) ( L ( в ПП ) ( МЕС ) ) ( I ( ТП or при_помощи РП or посредством РП ) ( ИНС ) ) )
        А как было бы лучше:
            O [ _ РП ] [ ЗАБ ]
            L [ в ПП ] [ МЕС ]
            I [ _ ТП , при_помощи РП , посредством РП ] [ ИНС ]
        Schemaless structure:
        [
            ('O', [('', 'РП')], ['ЗАБ']),
            ('L', [('в','ПП')], ['МЕС']),
            ('I', [('','ТП'),('при_помощи','РП'),('посредством','РП')], ['ИНС'])
        ]
        JSON-Schema structure:
        {
            "actants": [
                {
                    "actant_type": "O",
                    "syntax_template": [
                        {
                            "preposition": '',
                            "case": "РП"
                        }
                    ],
                    "semantic_categories": ["ЗАБ"]
                },
                {
                    "actant_type": "L",
                    "syntax_template": [
                        {
                            "preposition": "в",
                            "case": "ПП"
                        }
                    ],
                    "semantic_categories": ["МЕС"]
                },
                {
                    "actant_type": "I",
                    "syntax_template": [
                        {
                            "preposition": "",
                            "case": "ТП"
                        },
                        {
                            "preposition": "при_помощи",
                            "case": "РП"
                        },
                        {
                            "preposition": "посредством",
                            "case": "РП"
                        }
                    ],
                    "semantic_categories": ["ИНС"]
                }
            ]
        }
        """


def load_tasks():
    global TASKS_CORPUS
    global TASKS_TYPES_CORPUS

    filename = os.path.join(DICT_FOLDER, TASK_CORPUS_FILE)
    f = open(filename, 'r', encoding='utf-8')
    TASKS_TYPES_CORPUS = []
    TASKS_CORPUS = []
    for line in f:
        (type, task) = line.split(';', 1)
        TASKS_TYPES_CORPUS.append(type)
        TASKS_CORPUS.append(task)

    #print(TASKS_CORPUS)
    return (TASKS_CORPUS, TASKS_TYPES_CORPUS)


# Поиск парной закрывающей скобки с позиции s. Если не найдено, вернёт len(tokens)
def get_pair_parenthesis(tokens, s):
    f = s + 1
    stack = 0
    while f < len(tokens):
        if tokens[f] == '(':
            stack += 1
        if tokens[f] == ')':
            if stack == 0:
                return f
            stack -= 1
        f += 1
    return f


class DictionaryItem(ABC):
    """
    Абстрактная словарная статья
    """

    def __init__(self, word) -> None:
        self.word = word

    def __repr__(self):
        return self.word

    def __str__(self):
        return self.word

    def match(self, **kwargs):
        return False


class Dictionary(ABC):
    """
    Словарь
    """

    def __init__(self, dict_file) -> None:
        self.dict = {}
        self.dict_path = os.path.join(DICT_FOLDER, dict_file)

    def find(self, key) -> DictionaryItem:
        return self.dict.get(key)

    def form(self, canonical, part_of_speech, **kwargs):
        return None

    def save(self):
        f = open(self.dict_path, 'w', encoding='utf-8')
        for key in self.dict.keys():
            f.write(repr(self.dict[key]) + '\n')
        f.close()

    def print(self):
        for (root, item) in self.dict.items():
            print(item)


class ParameterItem(DictionaryItem):
    """
    Словарная статья параметра
    """

    def __init__(self, line) -> None:
        tokens = line.split(",")
        self.atom = tokens[0].strip()  # атом пролога
        self.name = tokens[1].strip()  # наименование

    def __repr__(self):
        return "{}, {}".format(self.atom, self.name)

    def __str__(self):
        return "{} {}".format(self.atom, self.name)


class ParametersDict(Dictionary):
    """
    Словарь параметро
    (атом, наименование)
    """

    def __init__(self) -> None:
        super().__init__(PARAMETERS_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            s = line.strip()
            if len(s) > 0 and not s.startswith('#'):
                u = ParameterItem(s)
                self.dict[u.name] = u
        f.close()


class UnitItem(DictionaryItem):
    """
    Словарная статья единицы измерения
    """

    def __init__(self, line) -> None:
        tokens = line.split(",")
        self.atom = tokens[0].strip()  # атом пролога
        self.code = tokens[1].strip()  # русское обозначение
        self.name = tokens[2].strip()  # Наименование единицы измерения

    def __repr__(self):
        return "{}, {}, {}".format(self.atom, self.code, self.name)

    def __str__(self):
        return "{} {} {}".format(self.atom, self.code, self.name)


class UnitsDict(Dictionary):
    """
    Словарь единиц измерения
    (atom, code, name)
    """

    def __init__(self) -> None:
        super().__init__(UNITS_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            s = line.strip()
            if len(s) > 0 and not s.startswith('#'):
                u = UnitItem(s)
                self.dict[u.name] = u
        f.close()

    def find_by_atom(self, atom) -> DictionaryItem:
        for v in self.dict.values():
            if v.atom == atom:
                return v
        return None


class SemanticCategoriesDict(Dictionary):
    """
    Словарь семантических категорий
    (код, описание)
    """

    def __init__(self) -> None:
        super().__init__(SEMANTIC_CATEGORIES_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            tokens = line.split()
            self.dict[tokens[0]] = tokens[1:]
        f.close()


class SynonymsDict(Dictionary):
    """
    Словарь синонимов:
    (лексема, {синоним}+)
    """

    def __init__(self) -> None:
        super().__init__(SYNONYMS_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            tokens = line.split()
            if len(tokens) == 0:
                continue
            self.dict[tokens[0]] = []
            for token in tokens[1:]:
                self.dict[tokens[0]].append(token)
        f.close()
        # self.save()

    def save(self):
        f = open(self.dict_path, 'w', encoding='utf-8')
        for key in self.dict.keys():
            s = key
            for synonym in self.dict[key]:
                s += " " + synonym
            f.write(s + '\n')
        f.close()

    def subst(self, word):
        """Замена слова на синоним"""
        for key in self.dict:
            for synset in self.dict[key]:
                if word in synset:
                    return key
        return word


class GluedWordsDict(Dictionary):
    """
    Словарь сложных лексем
    (сложная лексема)
    """

    def __init__(self) -> None:
        super().__init__(GLUED_WORDS_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            s = line.strip()
            if len(s) > 0:
                self.dict[s.replace(' ', '_')] = DictionaryItem(s)
        f.close()
        # self.save()

    def subst(self, s):
        for (key, item) in self.dict.items():
            s = s.replace(item.word, key)
        return s


class NonInflectedItem(DictionaryItem):
    """
    Словарная статья неизменяемого слова или словосочетания
    """

    def __init__(self, line) -> None:
        tokens = line.split()
        self.root = tokens[0]
        self.canonical = self.root
        self.part_of_speech = tokens[1]

    def __repr__(self):
        return "{} {}".format(self.root, self.part_of_speech)

    def __str__(self):
        return "{}, {}".format(self.root, PART_OF_SPEECH[self.part_of_speech])


class NonInflectedWordsDict(Dictionary):
    """
    Словарь готовых словоформ
    (словоформа, часть речи)
    """

    def __init__(self) -> None:
        super().__init__(NONINFLECTED_WORDS_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            item = NonInflectedItem(line)
            self.dict[item.root] = item
        f.close()
        # self.save()

    def save(self):
        f = open(self.dict_path, 'w', encoding='utf-8')
        for item in self.dict.values():
            f.write(repr(item) + '\n')
        f.close()


class CharacterItem(DictionaryItem):
    """
    Словарная статья характеристики
    """

    def __init__(self, line) -> None:
        tokens = line.split()
        self.root = tokens[0]
        self.flexion = tokens[1]
        if self.flexion == "_":
            self.flexion = ""
        self.canonical = self.root + self.flexion
        self.part_of_speech = tokens[2]
        self.inflection_type = tokens[3]

    def __repr__(self):
        f = self.flexion
        if f == "":
            f = "_"
        return "{} {} {} {}".format(self.root, f, self.part_of_speech, self.inflection_type)

    def __str__(self):
        return "{} {}, {}, {}".format(self.root, self.flexion, PART_OF_SPEECH[self.part_of_speech],
                                      self.inflection_type)


class Actant(object):
    """
        Описание шаблона актанта в модели управления
        Пример в словаре:
        ( I ( ТП or при_помощи РП or посредством РП ) ( ИНС ) )
        Возможный вариант в JSON
        {
                    "actant_type": "O",
                    "syntax_template": [
                        {
                            "preposition": '',
                            "case": "РП"
                        }
                    ],
                    "semantic_categories": ["ЗАБ"]
        }
    """

    def __init__(self, tokens):
        self.actant = tokens[0]
        self.syntax_template = []
        self.semantic_categories = []
        st_s = 1
        st_f = get_pair_parenthesis(tokens, st_s)
        self.parse_syntax_template(tokens[st_s + 1:st_f])
        sc_s = st_f + 1
        sc_f = get_pair_parenthesis(tokens, sc_s)
        self.parse_semantic_categories(tokens[sc_s + 1:sc_f])

    def parse_syntax_template(self, tokens):
        self.syntax_template = []
        s = 0
        while s < len(tokens):
            if tokens[s] == '|':
                s += 1
                continue

            if tokens[s] in CASE.keys():
                self.syntax_template.append(('', tokens[s]))
                s += 1
            else:
                self.syntax_template.append((tokens[s], tokens[s + 1]))
                s += 2

    def parse_semantic_categories(self, tokens):
        self.semantic_categories = []
        s = 0
        while s < len(tokens):
            if tokens[s] != '|':
                self.semantic_categories.append(tokens[s])
            s = s + 1

    def __repr__(self):
        st = ""
        for (preposition, case) in self.syntax_template:
            if preposition != "":
                st += preposition + " "
            st += case + " | "
        st = st[0:-3]  # уберём последний |
        sc = " | ".join(self.semantic_categories)
        return "( {} ( {} ) ( {} ) ) ".format(self.actant, st, sc)


class PredicateItem(DictionaryItem):
    """
    Словарная статья предиката
    """

    def __init__(self, line) -> None:
        tokens = line.split()
        self.canonical = tokens[0]
        self.actants = []
        self.parse_actants(tokens[1:])

    def repr_actants(self):
        s = "( "
        for actant in self.actants:
            s += repr(actant)
        return s + ")"

    def __repr__(self):
        return self.canonical + " " + self.repr_actants()

    def __str__(self):
        return self.canonical + ", " + self.repr_actants()

    def parse_actants(self, tokens):
        self.actants = []
        tokens = tokens[1:-1]  # выкидываем левую и правую общие скобки
        s = 0
        while s < len(tokens):
            f = get_pair_parenthesis(tokens, s)
            actant = Actant(tokens[s + 1:f])
            self.actants.append(actant)
            s = f + 1


class VerbItem(CharacterItem):
    """
    Словарная статья глагола
    """

    def __init__(self, line) -> None:
        super().__init__(line)


class EntityItem(CharacterItem):
    """
    Словарная статья понятия
    """

    def __init__(self, line) -> None:
        super().__init__(line)
        tokens = line.split()
        self.categories = []
        for token in tokens[5:-1]:  # семантические категории
            self.categories.append(token)

    def __repr__(self):
        return super().__repr__() + " [ " + " ".join(self.categories) + " ] "

    def __str__(self):
        return super().__str__() + " [ " + " ".join(self.categories) + " ] "


class BaseDictionary(Dictionary):
    """Класс для обслуживания словарей понятий, характеристик и глаголов"""

    def __init__(self, dict_file, item_classname, flexies) -> None:
        super().__init__(dict_file)
        self.flexies = flexies
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            item = item_classname(line)
            if item.root in self.dict:
                self.dict[item.root].append(item)
            else:
                self.dict[item.root] = [item]
        f.close()
        # self.save()

    def save(self):
        f = open(self.dict_path, 'w', encoding='utf-8')
        for key in self.dict.keys():
            for item in self.dict[key]:
                f.write(repr(item) + '\n')
        f.close()

    def find(self, word):
        # перебор разбиения слова на квазиоснову и квазифлексию
        quazi_base = word
        quazi_flexion = "_"
        while len(quazi_base) > 1:
            items = self.dict.get(quazi_base, [])
            for item in items:
                # print('match find {} {} {}'.format(item.root, item.flexion, item.inflection_type))
                flexions = self.flexies.find(quazi_flexion, item.part_of_speech, item.inflection_type)
                if len(flexions) > 0:
                    return item  # flexion TODO может списки возвращать?
            # Удлиняем квазифлексию и укорачиваем квазиоснову
            if quazi_flexion == "_":
                quazi_flexion = ""
            quazi_flexion = quazi_base[-1:] + quazi_flexion
            quazi_base = quazi_base[0:-1]
        return None

    def form(self, canonical, part_of_speech, **kwargs):
        for key in self.dict.keys():
            for item in self.dict[key]:
                if (item.part_of_speech == part_of_speech) and (item.canonical == canonical):
                    print('match form {} {} [{}]'.format(item.root, item.flexion, item.inflection_type))
                    flexion = self.flexies.form(item.root, part_of_speech, inflection_type=item.inflection_type,
                                                **kwargs)
                    if flexion is not None:
                        return item.root + flexion
                    else:
                        print("no flexion found")
        return None


class EntitiesDict(BaseDictionary):
    """
    Словарь понятий
    (квазиоснова, квазифлексия, часть речи, номер словоизменения, {семантическая категория}+)
    """

    def __init__(self, flexies) -> None:
        super().__init__(ENTITIES_DICT, EntityItem, flexies)


class CharactersDict(BaseDictionary):
    """
    Словарь характеристик
    (квазиоснова, квазифлексия, часть речи, номер словоизменения)
    """

    def __init__(self, flexies) -> None:
        super().__init__(CHARACTERS_DICT, CharacterItem, flexies)


class VerbsDict(BaseDictionary):
    """
    Словарь глаголов:
    (квазиоснова, квазифлексия, часть речи, номер словоизменения)
    """

    def __init__(self, flexies) -> None:
        super().__init__(VERBS_DICT, VerbItem, flexies)
        # self.save()


class PredicatesDict(Dictionary):
    """
    Словарь предикатов:
    (слово, модель управления)
    """

    def __init__(self) -> None:
        super().__init__(PREDICATES_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            item = PredicateItem(line)
            self.dict[item.canonical] = item
        f.close()
        # self.save()

    def save(self):
        f = open(self.dict_path, 'w', encoding='utf-8')
        for key, item in self.dict.items():
            f.write(repr(item) + '\n')
        f.close()


# тип словоизменения по Зализняку для квазифлексий
def get_inflection_types(line):
    types = re.match('.*\[(.*)\].*', line).group(1)
    tokens = types.split()
    result = []
    for token in tokens:
        result.append(token)
    return result


class NounFlexionItem(DictionaryItem):
    """
    МИ квазифлексии существительного и полного прилагательного
    (род, падеж, число, {номер словоизменения}+)
    """

    def __init__(self, line) -> None:
        tokens = line.split()
        self.flexion = tokens[0]
        if self.flexion == "_":
            self.flexion = ""
        self.part_of_speech = tokens[1]
        self.gender = tokens[2]
        self.case = tokens[3]
        self.number = tokens[4]
        self.inflection_types = get_inflection_types(line)

    def __repr__(self):
        f = self.flexion
        if f == "":
            f = "_"
        return "{} {} {} {} {} [ {} ]".format(f,
                                              self.part_of_speech,
                                              self.gender,
                                              self.case,
                                              self.number,
                                              " ".join(self.inflection_types))

    def __str__(self):
        return "{}, {}, {}, {}, {}".format(self.flexion,
                                           PART_OF_SPEECH[self.part_of_speech],
                                           GENDER[self.gender],
                                           CASE[self.case],
                                           NUMBER[self.number]
                                           )

    def match(self, part_of_speech, **kwargs):
        return self.part_of_speech == part_of_speech and \
               self.gender == kwargs["gender"] and \
               self.case == kwargs["case"] and \
               self.number == kwargs["number"] and \
               kwargs["inflection_type"] in self.inflection_types


class ShortAdjectiveFlexionItem(DictionaryItem):
    """
    МИ квазифлексии краткого прилагательного:
    (род, число, {номер словоизменения}+)
    """

    def __init__(self, line) -> None:
        tokens = line.split()
        self.flexion = tokens[0]
        if self.flexion == "_":
            self.flexion = ""
        self.part_of_speech = tokens[1]
        self.gender = tokens[2]
        self.number = tokens[3]
        self.inflection_types = get_inflection_types(line)

    def __repr__(self):
        f = self.flexion
        if f == "":
            f = "_"
        return "{} {} {} {} [ {} ]".format(f,
                                           self.part_of_speech,
                                           self.gender,
                                           self.number,
                                           " ".join(self.inflection_types))

    def __str__(self):
        return "{}, {}, {}, {}".format(self.flexion,
                                       PART_OF_SPEECH[self.part_of_speech],
                                       GENDER[self.gender],
                                       NUMBER[self.number]
                                       )

    def match(self, part_of_speech, **kwargs):
        return self.part_of_speech == part_of_speech and \
               self.gender == kwargs["gender"] and \
               self.number == kwargs["number"] and \
               kwargs["inflection_type"] in self.inflection_types


class ParticipleFlexionItem(DictionaryItem):
    """
    МИ квазифлексии деепричастия:
    (время, вид, {номер словоизменения}+)
    """

    def __init__(self, line) -> None:
        tokens = line.split()
        self.flexion = tokens[0]
        if self.flexion == "_":
            self.flexion = ""
        self.part_of_speech = tokens[1]
        self.tense = tokens[2]
        self.aspect = tokens[3]
        self.inflection_types = get_inflection_types(line)

    def __repr__(self):
        f = self.flexion
        if f == "":
            f = "_"
        return "{} {} {} {} [ {} ]".format(f,
                                           self.part_of_speech,
                                           self.tense,
                                           self.aspect,
                                           " ".join(self.inflection_types))

    def __str__(self):
        return "{}, {}, {}, {}".format(self.flexion,
                                       PART_OF_SPEECH[self.part_of_speech],
                                       TENSE[self.tense],
                                       ASPECT[self.aspect]
                                       )

    def match(self, part_of_speech, **kwargs):
        return self.part_of_speech == part_of_speech and \
               self.tense == kwargs["tense"] and \
               self.aspect == kwargs["aspect"] and \
               kwargs["inflection_type"] in self.inflection_types


class VerbFlexionItem(DictionaryItem):
    """
    МИ квазифлексии глагола:
    (время, лицо, род, число, вид, {номер словоизменения}+)
    """

    def __init__(self, line) -> None:
        tokens = line.split()
        self.flexion = tokens[0]
        if self.flexion == "_":
            self.flexion = ""
        self.part_of_speech = tokens[1]
        self.tense = tokens[2]
        self.person = tokens[3]
        self.gender = tokens[4]
        self.number = tokens[5]
        self.aspect = tokens[6]
        self.inflection_types = get_inflection_types(line)

    def __repr__(self):
        f = self.flexion
        if f == "":
            f = "_"
        return "{} {} {} {} {} {} {} [ {} ]".format(f,
                                                    self.part_of_speech,
                                                    self.tense,
                                                    self.person,
                                                    self.gender,
                                                    self.number,
                                                    self.aspect,
                                                    " ".join(self.inflection_types))

    def __str__(self):
        return "{}, {}, {}, {}, {}, {}, {}".format(self.flexion,
                                                   PART_OF_SPEECH[self.part_of_speech],
                                                   TENSE[self.tense],
                                                   PERSON[self.person],
                                                   GENDER[self.gender],
                                                   NUMBER[self.number],
                                                   ASPECT[self.aspect]
                                                   )

    def match(self, part_of_speech, **kwargs):
        return self.part_of_speech == part_of_speech and \
               self.tense == kwargs["tense"] and \
               self.person == kwargs["person"] and \
               (self.gender == kwargs["gender"] or self.gender == 'НР') and \
               self.number == kwargs["number"] and \
               self.aspect == kwargs["aspect"] and \
               kwargs["inflection_type"] in self.inflection_types


# связывание с классами для частей речи, у которых могут быть окончания
FLEXION_TYPE = {
    "СУ": NounFlexionItem,
    "ПП": NounFlexionItem,
    "КП": ShortAdjectiveFlexionItem,
    "ДЕ": ParticipleFlexionItem,
    "ГЛ": VerbFlexionItem}


class FlexiesDict(Dictionary):
    """
    Словарь квазифлексий
    (квазифлексия, часть речи, МИ, {номер словоизменения}+)
    МИ = род падеж число | род число | время вид | время лицо род число вид
    """

    def __init__(self) -> None:
        super().__init__(FLEXIES_DICT)
        f = open(self.dict_path, encoding='utf-8')
        for line in f:
            line = line.strip()
            if len(line) > 0:
                tokens = line.split()
                flexion = tokens[0]
                part_of_speech = tokens[1]
                if part_of_speech in FLEXION_TYPE:
                    item_classname = FLEXION_TYPE[part_of_speech]
                    item = item_classname(line)
                    if flexion in self.dict:
                        self.dict[flexion].append(item)
                    else:
                        self.dict[flexion] = [item]
                    # print(repr(item))
        f.close()
        # print(len(self.dict))
        # self.save()

    def save(self):
        f = open(self.dict_path, 'w', encoding='utf-8')
        for key in self.dict.keys():
            for item in self.dict[key]:
                f.write(repr(item) + '\n')
        f.close()

    def find(self, flexion, part_of_speech, inflection_type) -> list:
        """Поиск квазифлексии, соответствующей образцу, части речи и типу словоизменения"""
        if self.dict.get(flexion) is None:
            return []
        return list(
            filter(lambda x: x.part_of_speech == part_of_speech and inflection_type in x.inflection_types,
                   self.dict.get(flexion)))

    def form(self, root, part_of_speech, **kwargs):
        """Подбор подходящей квазифлексии для указанной квазиосновы и морфологической информации"""
        # надо словарь сделать фильтруемым по морфологической информации
        # print('searching flexion for ' + root + ' ' + part_of_speech)
        for key in self.dict.keys():
            lst = list(filter(lambda x: type(x) == FLEXION_TYPE[part_of_speech], self.dict[key]))
            for item in lst:
                if item.match(part_of_speech, **kwargs):
                    # print("matched flexion: " + str(item))
                    return item.flexion
        return None

