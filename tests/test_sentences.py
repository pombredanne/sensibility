#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2017 Eddie Antonio Santos <easantos@ualberta.ca>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tests the generation of sentences.
"""

import pytest  # type: ignore

from sensibility.sentences import forward_sentences, backward_sentences
from sensibility.language.javascript import javascript


def test_forward_sentences(test_file, vocabulary) -> None:
    """
    Test creating padded forward sentences.
    """
    n = 10  # sentence length.
    m = n - 1  # context length.

    sentences = list(forward_sentences(test_file, context=m))

    # Even with padding, there should be the same number of sentences as there
    # are tokens in the original vector.
    assert len(sentences) == len(test_file)

    # Test each sentence generated.
    for i, (context, adjacent) in enumerate(sentences):
        assert len(context) == m
        assert adjacent == test_file[i]

    # The first context should be a context with all padding.
    context, adjacent = sentences[0]
    assert all(index == vocabulary.start_token_index for index in context)


def test_forward_sentences_too_big(test_file, vocabulary) -> None:
    """
    test for when sentence size is LARGER than file
    """
    n = 20
    sentences = list(forward_sentences(test_file, context=n))

    # There should be the same number of sentences as tokens.
    assert len(sentences) == len(test_file)

    # The first context should be a context with all padding.
    context, adjacent = sentences[0]
    assert adjacent == test_file[0]
    assert len(context) == n
    assert all(index == vocabulary.start_token_index for index in context)

    # Check the last sentence
    context, adjacent = sentences[-1]
    assert adjacent == test_file[-1]
    # It should still have padding!
    padding = context[:-len(test_file) - 1]
    assert len(padding) > 0
    assert all(index == vocabulary.start_token_index for index in padding)


def test_backward_sentences(test_file, vocabulary) -> None:
    """
    Test creating padded backwards sentences.
    """
    n = 10  # sentence length.
    m = n - 1  # context length.

    sentences = list(backward_sentences(test_file, context=m))

    # Even with padding, there should be the same number of sentences as there
    # are tokens in the original vector.
    assert len(sentences) == len(test_file)

    # Test each sentence generated.
    for i, (context, adjacent) in enumerate(sentences):
        assert adjacent == test_file[i]
        assert len(context) == m, str(i) + ': ' + vocabulary.to_text(adjacent)

    # The first context should be all NON padding!
    context, adjacent = sentences[0]
    assert all(index != vocabulary.end_token_index for index in context)

    # The last context should be a context with all padding.
    context, adjacent = sentences[-1]
    assert all(index == vocabulary.end_token_index for index in context)


def test_both_sentences(test_file):
    args = (test_file,)
    kwargs = dict(context=9)
    combined = zip(forward_sentences(*args, **kwargs),
                   backward_sentences(*args, **kwargs))

    # Check if both adjacent are THE SAME.
    for (_, t1), (_, t2) in combined:
        assert t1 == t2


@pytest.fixture
def test_file():
    """
    Parses a sample file with exactly 13 tokens!
    """
    entries = list(javascript.vocabularize(r'''
        (name) => console.log(`Hello, ${name}!`);
    '''))
    assert len(entries) == 13
    return entries


@pytest.fixture
def vocabulary():
    return javascript.vocabulary
