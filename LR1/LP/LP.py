# -*- coding: utf-8 -*-
from LP.Dictionaries import *
from LP.Consts import *
from copy import deepcopy
import pymorphy2


class Variant(object):
    """
    Вариант разбора слова
    """

    def __init__(self) -> None:
        self.word = ""
        self.root_item = None  # потомок DictionaryItem для основ
        self.flexion_item = None  # потомок DictionaryItem для флексий
        self.dictionary = ""

        self.predicate_item = None  # связь с предикатом PredicateItem
        self.actant = None  # связь с актантом предиката Actant
        self.category = ""  # семантическая категория связи
        self.preposition = ""  # предлог связи
        self.case = ""  # падеж связи

        self.characterized_item = None  # связь характеристики с понятием

    def __repr__(self):
        return "{}, {}, -{}".format(
            self.root_item.canonical,
            self.root_item.part_of_speech,
            repr(self.flexion_item)
        )

    def __str__(self):
        return "{}, {}, -{}".format(
            self.root_item.canonical,
            self.root_item.part_of_speech,
            str(self.flexion_item)
        )


class LinguisticProcessor(object):
    units = UnitsDict()
    parameters = ParametersDict()
    gwd = GluedWordsDict()
    scd = SemanticCategoriesDict()
    niwd = NonInflectedWordsDict()
    synd = SynonymsDict()
    # сначала загружается словарь квазифлексий, потом использующие его словари изменяемых слов
    flexies_dict = FlexiesDict()
    dicts = [EntitiesDict(flexies_dict), CharactersDict(flexies_dict), VerbsDict(flexies_dict)]
    preds = PredicatesDict()

    def print_dicts(self):
        """Печать слов из Dictionaries с информацией из словаря OpenCorpora"""
        morph = pymorphy2.MorphAnalyzer()
        for d in self.dicts:
            for (root, items) in d.dict.items():
                for item in items:
                    variants = morph.parse(item.canonical)
                    if len(variants) > 0:
                        for v in variants:
                            print("{}: {} OpenCorpora({})".format(
                                item.canonical,
                                v.normal_form,
                                v.tag.cyr_repr))
                    else:
                        print(item.canonical + ' - не найдено')

    def find(self, word):
        # сначала пробуем найти среди неизменяемых слов
        item = self.niwd.find(word)
        if item is not None:
            return word + ': ' + str(item)
        # поиск в словарях изменяемых слов с разбиением слова на квазиоснову и квазифлексию
        root = word
        flexion = "_"
        while len(root) > 1:
            for dict in self.dicts:
                lst = dict.dict.get(root, [])
                for item in lst:
                    # найдём МИ в словаре флексий
                    lst = self.flexies_dict.find(flexion, item.part_of_speech, item.inflection_type)
                    for flexion_item in lst:
                        print('flexion ' + str(flexion_item))
                    return word + ': ' + item.canonical + ' ' + item.part_of_speech  # + ' ' + str(flexion_item)
            # Удлиняем квазифлексию и укорачиваем квазиоснову
            if flexion == "_":
                flexion = ""
            flexion = root[-1:] + flexion
            root = root[0:-1]
        return word + ": Неопределенная часть речи"

    def parse_tokens(self, tokens):
        lexemes = []
        for word in tokens:
            word_variants = []
            # сначала пробуем найти среди неизменяемых слов
            item = self.niwd.find(word)
            if item is not None:
                v = Variant()
                v.word = word
                v.root_item = deepcopy(item)
                v.dictionary = type(self.niwd)
                word_variants.append(v)

            # поиск в словарях изменяемых слов с разбиением слова на квазиоснову и квазифлексию
            # могут найтись разные допустимые варианты разбиения в разных словарях
            root = word
            flexion = "_"
            while len(root) > 1:
                for dict in self.dicts:
                    roots = dict.dict.get(root, [])
                    for item in roots:
                        # найдём МИ в словаре флексий
                        flexies = self.flexies_dict.find(flexion, item.part_of_speech, item.inflection_type)
                        for flexion_item in flexies:
                            v = Variant()
                            v.word = word
                            v.root_item = deepcopy(item)
                            v.flexion_item = deepcopy(flexion_item)
                            v.dictionary = type(dict)
                            word_variants.append(v)
                # Удлиняем квазифлексию и укорачиваем квазиоснову
                if flexion == "_":
                    flexion = ""
                flexion = root[-1:] + flexion
                root = root[0:-1]
            lexemes.append((word, word_variants))
        return lexemes

    def parse(self, phrase):
        phrase = self.gwd.subst(phrase)  # выявляются сложные лексемы, в которых пробелы заменяютс на _
        self.parse_tokens(phrase.split())

    def get_predicate(self, lexemes):
        """
        Находит предикат предложения
        :param lexemes:
        :return: PredicateItem
        """
        predicate_item = None
        for lexeme, variants in lexemes:
            for v in variants:
                if isinstance(v.root_item, PredicateItem):
                    # части речи предикатов по убыванию приоритета: ГЛ, СУ, ДЕ
                    if predicate_item is None:
                        predicate_item = v.root_item
                    elif (predicate_item.part_of_speech == "ДЕ") and (v.root_item.part_of_speech != "ДЕ") or \
                            (predicate_item.part_of_speech == "СУ") and (v.root_item.part_of_speech == "ГЛ"):
                        predicate_item = v.root_item
        return predicate_item

    def form(self, canonical, part_of_speech, **kwargs):
        # валидация параметров
        for (key, value) in kwargs.items():
            if value not in MORPHOLOGY_ITEM_DICT[key]:
                print('Несуществующее значение {} параметра {}'.format(value, key))
                return None
        # если всё хорошо, начинаем искать
        for d in self.dicts:
            res = d.form(canonical, part_of_speech, **kwargs)
            if res is not None:
                return res
        return canonical + " - Подходящей словоформы не найдено"


def harmonized(character_variant, entity_variant):
    """
    Проверка согласованности характеристики и понятия
    :param character_variant: Variant
    :param entity_variant: Variant
    :return: bool
    """
    if not isinstance(character_variant.flexion_item, NounFlexionItem) or \
            not isinstance(entity_variant.flexion_item, NounFlexionItem):
        return False

    if character_variant.flexion_item is None or entity_variant.flexion_item is None:
        return True

    if character_variant.flexion_item.number == entity_variant.flexion_item.number and \
            character_variant.flexion_item.gender == entity_variant.flexion_item.gender and \
            character_variant.flexion_item.case == entity_variant.flexion_item.case:
        return True
    return False


def precedes(lexemes, preposition, lexeme):
    """
    Проверяет предшествование предлога и лексемы
    :param lexemes: list of (word, variants)
    :param preposition: string
    :param lexeme: string
    :return: bool
    """
    # пустой предлог всегда предшествует лексеме
    if len(preposition) == 0:
        return True

    if preposition not in lexemes:
        return False

    # проверим непустой предлог
    tokens = [i for i, j in lexemes]
    i = tokens.index(preposition)
    j = tokens.index(lexeme)
    if 0 < j-i:
        return True
    return False


def link_entity_with_characteristics(lexemes):
    """
    установление связей "понятие-характеристика"
    :param lexemes: list of (word, variants)
    :return:
    """
    for i in range(len(lexemes) - 1):
        for character_variant in lexemes[i][1]:
            for entity_variant in lexemes[i + 1][1]:
                if harmonized(character_variant, entity_variant):
                    # свяжем характеристику с понятием
                    character_variant.characterized_item = entity_variant.root_item


def link_predicate_with_actants(lexemes, predicate_item):
    """
    установление связей "предикат-актант"
    :param lexemes: list of (word, variants)
    :param predicate_item: PredicateItem
    :return:
    """
    # для каждого актанта подберём подходящее слово
    for actant in predicate_item.actants:
        # каждое слово померяем под ограничения актанта (семантическую категорию и падеж)
        for lexeme, variants in lexemes:
            for v in variants:
                if v.root_item == predicate_item:
                    # пропускаем наш предикат
                    continue
                if isinstance(v.root_item, EntityItem):
                    # если семантическая категория подходит
                    categories = list(set(actant.semantic_categories) & set(v.root_item.categories))
                    if len(categories) > 0:
                        for (preposition, case) in actant.syntax_template:
                            # если падеж подходит
                            if case == v.flexion_item.case and precedes(lexemes, preposition, lexeme):
                                # привяжем к слову связь с актантом предиката
                                v.predicate_item = deepcopy(predicate_item)
                                v.actant = deepcopy(actant)  # лучше его сконструировать
                                v.category = categories[0]
                                v.preposition = preposition
                                v.case = case
                                # пометим слово как связанное?


def print_triples(lexemes):
    """
    Печать триплетов Субъект-Отношение-Объект
    :param lexemes: lists of (word, variants)
    :return:
    """
    for lexeme, variants in lexemes:
        for v in variants:
            if isinstance(v.root_item, PredicateItem):
                print("(:predicate {})".format(v.root_item.canonical))
            elif isinstance(v.root_item, EntityItem):
                if v.actant is not None:
                    print("({} :{} of {}) ({})".format(
                        v.root_item.canonical,
                        ACTANT_TYPE[v.actant.actant],
                        v.predicate_item.canonical,
                        v.category))
            elif isinstance(v.root_item, CharacterItem):
                if v.characterized_item is not None:
                    print("({} :characterizes {}) ({} {} {})".format(
                        v.root_item.canonical,
                        v.characterized_item.canonical,
                        v.flexion_item.gender,
                        v.flexion_item.number,
                        v.flexion_item.case))

