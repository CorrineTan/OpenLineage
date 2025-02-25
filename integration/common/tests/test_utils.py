# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from openlineage.common.utils import get_from_nullable_chain, parse_single_arg


def test_nullable_chain_fails():
    x = {"first": {"second": {}}}
    assert get_from_nullable_chain(x, ['first', 'second', 'third']) is None


def test_nullable_chain_works():
    x = {"first": {"second": {"third": 42}}}
    assert get_from_nullable_chain(x, ['first', 'second', 'third']) == 42

    x = {"first": {"second": {"third": 42, "fourth": {"empty": 56}}}}
    assert get_from_nullable_chain(x, ['first', 'second', 'third']) == 42


def test_parse_single_arg_does_not_exist():
    assert parse_single_arg(['dbt', 'run'], ['-t', '--target']) is None
    assert parse_single_arg(['python', 'main.py', '--random_arg', 'yes'], ['--what']) is None


def test_parse_single_arg_next():
    assert parse_single_arg(['dbt', 'run', '--target', 'prod'], ['-t', '--target']) == 'prod'
    assert parse_single_arg(['python', '--random=yes', '--what', 'asdf'], ['--what']) == 'asdf'


def test_parse_single_arg_equals():
    assert parse_single_arg(['dbt', 'run', '--target=prod'], ['-t', '--target']) == 'prod'
    assert parse_single_arg(['python', '--random=yes', '--what=asdf'], ['--what']) == 'asdf'


def test_parse_single_arg_gets_first_key():
    assert parse_single_arg(['dbt', 'run', '--target=prod', '-t=a'], ['-t', '--target']) == 'a'


def test_parse_single_arg_default():
    assert parse_single_arg(['dbt', 'run'], ['-t', '--target']) is None
    assert parse_single_arg(['dbt', 'run'], ['-t', '--target'], default='prod') == 'prod'
