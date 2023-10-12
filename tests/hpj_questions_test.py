
from copy import copy
from typing import List, Self
import unittest

from hpj_questions import Questions, build_questions
from survey.question_base import CustomValidatedQuestion, IQuestion, OptionQuestion


class Tree:
    def __init__(self, name: object, children: List[Self]) -> None:
        self.name = name
        self.children = children

    @property
    def key(self):
        return self.question_source[self.name]

    @property
    def is_last_node(self):
        return self.children == []

    def search_loops(self, prev_nodes: list = []) -> list:
        prev_nodes.append(self.name)

        if self.name in prev_nodes[:-1]:
            return prev_nodes

        result = []
        for child in self.children:
            child_res = child.search_loops(copy(prev_nodes))
            if child_res:
                result.append(child_res)

        return result

    def search_unique_nodes(self, nodes: set = set()):
        nodes.add(self.name)
        for child in self.children:
            child.search_unique_nodes(nodes)

        return nodes


def recursion_limiter(limit: int = -1):

    def deco(func):
        func.limit = limit

        def wrapper(*args, **kwargs):
            func.limit -= 1
            if func.limit == 0:
                raise RecursionError
            result = func(*args, **kwargs)
            func.limit += 1
            return result

        return wrapper

    return deco


class HpjQuestionsTest(unittest.TestCase):

    def test_all_questions_declared(self):
        hpj_built_questions = build_questions()
        self.assertSetEqual(set(hpj_built_questions.keys()), set(Questions))

    def test_custom_validated_question_has_no_options(self):
        def check_options(question) -> bool:
            return isinstance(question, CustomValidatedQuestion) and not question.options

        self.assertFalse(any(map(check_options, build_questions().values())))

    def test_option_questions_dont_return_self(self):
        def check_options(question) -> bool:
            if not isinstance(question, OptionQuestion):
                return False

            return IQuestion.SAME in map(lambda x: question.reply(x), question.options)

        self.assertFalse(any(map(check_options, build_questions().values())))

    def test_questions_correct_return(self):
        hpj_question = build_questions()
        possible_replies = set(hpj_question.keys())
        possible_replies.add(IQuestion.END)

        def check_replies(question) -> bool:
            options = question.options or ['test']
            next_questions = set(map(lambda x: question.reply(x), options))
            return bool(next_questions - possible_replies)

        self.assertFalse(any(map(check_replies, hpj_question.values())))

    def _build_question_tree(self) -> Tree:
        hpj_questions = build_questions()

        @recursion_limiter(len(hpj_questions) * 10)
        def build_tree(question_key) -> Tree:
            assert question_key != IQuestion.SAME

            if question_key == IQuestion.END:
                return Tree(question_key, [])

            question = hpj_questions[question_key]
            answers = question.options or ['test']
            children = list(set(question.reply(ans) for ans in answers))

            return Tree(question_key, [build_tree(child) for child in children])

        return build_tree(Questions.Date)

    def test_search_loops(self):
        tree_root = self._build_question_tree()
        self.assertFalse(any(tree_root.search_loops()))

    def test_have_non_traversable_questions(self):
        tree_root = self._build_question_tree()
        hpj_questions = set(build_questions().keys())
        self.assertFalse(bool(hpj_questions - tree_root.search_unique_nodes()))
