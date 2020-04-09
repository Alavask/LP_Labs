# -*- coding: utf-8 -*-
import pymorphy2
from LP.LP import *


def lp_ex(tokens):

    lp = LinguisticProcessor()

    # найдём предикаты
    '''
    for word, variants in lexemes:
        parse = variants[0]
        predicate_item = lp.preds.find(parse.normal_form)
        if predicate_item is not None:
            print("{} {}".format(word, predicate_item.repr_actants()))
            pass
    '''

    lplexems = lp.parse_tokens(tokens)
    # print(lexemes)
    for lexeme, variants in lplexems:
        print(lexeme)
        for v in variants:
            print("  " + str(v))
            if isinstance(v.root_item, PredicateItem):
                if v.root_item.actants is not []:
                    print("  " + repr(v.root_item.actants))

    predicate_item = lp.get_predicate(lplexems)
    print("Предикат: " + str(predicate_item) + "\n")

    # TODO: сломалось
    # LP.link_entity_with_characteristics(lplexems)
    # LP.link_predicate_with_actants(lplexems, predicate_item)

    print("\nСвязи:")
    print_triples(lplexems)


def pymorphy_ex(tokens):
    morph = pymorphy2.MorphAnalyzer()
    for token in tokens:
        variants = morph.parse(token)
        if len(variants) > 0:
            for v in variants:
                print("{}: {} OpenCorpora({})".format(
                    token,
                    v.normal_form,
                    v.tag.cyr_repr))
        else:
            print(token + ' - не найдено')


if __name__ == "__main__":
    text = 'Построение плана выхода из себя или из кризиса'

    import razdel  # https://github.com/natasha/razdel

    # import razdel.sentenize
    # в razdel есть sentenize и tokenize
    # rules = razdel.rule.RULES
    # rules.remove(razdel.sentenize.FunctionRule(razdel.sentenize.initials_left))
    # sentences = [_.text for _ in list(razdel.sentenize(text, rules=rules))]
    sentences = [_.text for _ in list(razdel.sentenize(text))]
    print(sentences)
    tokens = [_.text for _ in list(razdel.tokenize(text.lower()))]  # text.lower()
    print(tokens)

    lp_ex(tokens)
    pymorphy_ex(tokens)
