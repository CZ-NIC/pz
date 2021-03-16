import logging
import sys
import unittest
from subprocess import Popen, PIPE, STDOUT, DEVNULL
from time import time
from typing import Optional

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

CSV = """Wyatt Madden|Kiayada Briggs|Jamaica|Trento
Otto Lindsay|Cooper Hebert|Austria|Oud-Turnhout
Mallory Barton|Kirestin Nolan|Moldova|Orilla
Blaine Fleming|Skyler Hester|Bosnia and Herzegovina|Mercedes
Natalie Logan|Brooke Sampson|United States Minor Outlying Islands|Hamburg
Bree Roman|Davis Raymond|South Georgia and The South Sandwich Islands|Llaillay
Alexander Finley|Wynter Branch|Moldova|Pumanque
Tasha Thompson|Lydia Reynolds|Lebanon|Volgograd
Clayton Byers|Shellie Stafford|Belgium|Stonehaven
Maisie Crane|Fleur Griffin|Liechtenstein|Sahiwal
"""

LOREM = """Lorem ipsum dolor sit amet http://example.com consectetur http://csirt.cz
https://example.org
adipiscing elit http://nic.cz http://example.com
sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
"""

forgotten_text = "Did you not forget to use --whole to access `text`?"
exc_text = "Exception: <class 'NameError'> name 'text' is not defined on line: "


class TestMaster(unittest.TestCase):
    col2 = 's.split("|")[2]'

    def go(self, command="", piped_text=None, previous_command=None, empty=False, n=None, text=False, custom_cmd=None,
           expect=None, debug=False, verbosity=0, quiet=False, setup=None, end=None, sub=None, format=False,
           generate: Optional[str] = None, stderr=STDOUT):
        """

        @param command:
        @param piped_text:
        @param previous_command:
        @param empty:
        @param n:
        @param text:
        @param custom_cmd:
        @param expect:
        @param debug:
        @param verbosity:
        @param quiet:
        @param setup:
        @param end:
        @param sub:
        @param generate: The generate clause
        @param stderr:
        @return:
        """
        cmd = ["./pz", command]
        if empty:
            cmd.append("--empty")
        if n:
            cmd.extend(("-n", str(n)))
        if text:
            cmd.append("--whole")
        if custom_cmd:
            cmd.append(custom_cmd)
        if verbosity:
            cmd.extend(["-v"] * verbosity)
        if quiet:
            cmd.append("-q")
        if setup:
            cmd.extend(["--setup", setup])
        if end:
            cmd.extend(["--end", end])
        if sub:
            cmd.extend(["--sub", sub])
        if format:
            cmd.append("--format")
        if generate is not None:
            cmd.append("--generate")  # this flag might be empty as it has a default value
            if generate:
                cmd.append(generate)

        if previous_command:
            cmd[1] = f"'{cmd[1]}'"  # this is the main command clause, need to quote while text-joining
            cmd = previous_command + " | " + " ".join(cmd)

        if debug:
            print("Command", cmd)

        if previous_command:
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=stderr)
            stdout = p.communicate()[0]
        elif piped_text:
            if isinstance(piped_text, list):
                piped_text = "\n".join(piped_text)
            elif not isinstance(piped_text, str):
                piped_text = str(piped_text)
            p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=stderr)
            stdout = p.communicate(input=piped_text.encode("utf-8"))[0]
        elif generate is not None:
            p = Popen(cmd, stdout=PIPE, stderr=stderr)
            stdout = p.communicate()[0]
        else:
            raise AttributeError("Specify either piped_text, previous_command or generate")

        val = stdout.decode().rstrip().splitlines()
        if debug:
            print(val)
        if expect is not None:
            if isinstance(expect, list):
                self.assertListEqual(expect, val)
            else:
                self.assertEqual([str(expect)], val)

        return val

    def test_delayed_input(self):
        """ Sleep function works, must rend execution longer """

        start = time()
        self.go("sleep(1)", piped_text=1)
        self.assertTrue(1 < (time() - start) < 2)

        start = time()
        self.go("s", piped_text=1)
        self.assertTrue((time() - start) < 1)


class TestFlags(TestMaster):

    def test_number_of_lines(self):
        self.assertEqual(3, len(self.go(self.col2, CSV, n=3)))

    def test_import(self):
        # log should be already present due to `from math import *`
        self.go('log(n)', previous_command="echo '1000'", expect='6.907755278982137')

        # timedelta should be importable in the setup
        self.go(r's+=str(timedelta(seconds=5))', piped_text="123", custom_cmd="-vv",
                setup="from datetime import timedelta",
                expect="1230:00:05")

        # when verbosity increased, we should get notified when an import happened
        self.go(r'Path("/")', previous_command="echo '123'", verbosity=0, expect='/')
        self.go(r'Path("/")', previous_command="echo '123'", verbosity=1,
                expect=['Changing the main clause to: s = Path("/")', 'Importing Path from pathlib', '/'])

    def test_failed_line(self):
        """ Exceptions are shown only if verbosity active. They are correctly printed to STDERR.
        (Note that self.go will pipe STDERR to STDOUT too, hence we do not use it here.)
        """

        def check(verbosity=0, quiet=0, expect_stderr=b''):
            p = Popen(["./pz", "invalid line"] + ["-v"] * verbosity + ["-q"] * quiet,
                      stdout=PIPE, stdin=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate(input=b"1")

            self.assertEqual(b'', stdout)
            self.assertEqual(expect_stderr, stderr)

        auto_import_text = b"Changing the main clause to: s = invalid line\n"
        exception_text = b"Exception: <class 'SyntaxError'> invalid syntax (<string>, line 1) on line: 1\n"
        check(quiet=1)
        check(verbosity=0, expect_stderr=exception_text)
        check(verbosity=1, expect_stderr=auto_import_text + exception_text)

    def test_debugging(self):
        """ No access to `text` variable. (Not fetched by --text, should produce an invisible exception.) """
        # verbosity 0
        self.go(r"len(text)", LOREM, n=1, quiet=True)

        # increased verbosity
        self.go(r"len(text)", LOREM, n=1, verbosity=0,
                expect=[forgotten_text,
                        exc_text + "Lorem ipsum dolor sit amet http://example.com consectetur http://csirt.cz"])

    def test_filter(self):
        expect = [line for line in LOREM.splitlines() if len(line) > 20]
        r = self.go(r"len(s) > 20", LOREM, custom_cmd="--filter", expect=expect)
        self.assertEqual(3, len(r))

    def test_setup(self):
        self.assertEqual(4, len(self.go("if custom: skip=True;", LOREM, setup='custom = 0;')))
        self.assertEqual(0, len(self.go("if custom: skip=True;", LOREM, setup='custom = 1;')))

    def test_empty(self):
        """ `s = ` is prepended and empty lines are kept """
        self.go(self.col2 + ' == "Jamaica"', CSV, empty=True, expect=['True'] + ['False'] * 9)

    def test_skip_all(self):
        """ flag `-0` works however it can be overriden by using `skip` variable """
        # lines are output normally
        self.go("s", "1\n2\n2\n3", expect=["1", "2", "2", "3"])
        # when -0, no lines are shown
        self.go("s", "1\n2\n2\n3", expect=[], custom_cmd="-0")
        # however, this behaviour is overriden by using `skip`
        self.go("skip = s == '2'", "1\n2\n2\n3", expect=["1", "3"], custom_cmd="-0")
        # `skip` can override just some cases, others remain skipped through `-0` by default
        self.go("if s == '2': skip = False", "1\n2\n2\n3", expect=["2", "2"], custom_cmd="-0")

    def test_text(self):
        """ The `text` variable is available during processing only when the flag `--whole`
         is on or always in the `end` clause. """
        self.go(end="len(text)", piped_text="hello", expect=5, text=False)
        self.go(end="len(text)", piped_text="hello", expect=5, text=True)
        self.go("len(text)", piped_text="hello", expect=5, text=True)
        self.go("len(text)", piped_text="hello", expect=[], text=False, quiet=True)

    def test_format(self):
        """ Formatting flag influences both main clause and the end clause. """
        self.go("{n+3} %", format=True, piped_text="5", expect="8 %")
        self.go(end="{sum(numbers)+3} %", format=True, piped_text="5\n2", expect="10 %")
        self.go("{n}: {factorial(n)}", format=True, generate="5", expect=["1: 1", "2: 2", "3: 6", "4: 24", "5: 120"])

    def test_stderr(self):
        """ When using --stderr flag, the contents piped to STDOUT must stay intact. """
        def _test(cmd):
            return Popen(["./pz", "--end", "'end'"] + cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE).communicate(b"1")
        self.assertEqual((b'1\nend\n', b''), _test(["s"]))
        self.assertEqual((b'1\n', b'1\nend\n'), _test(["s", "--stderr"]))
        self.assertEqual((b'1\n', b'3\nend\n'), _test(["n+2", "--stderr"]))


class TestVariables(TestMaster):
    # # deprecated
    # def test_lines(self):
    #     """ Possibility to use `lines` list instead of re-assigning `line`. """
    #     self.assertListEqual(['5'] * 4, self.go(r"lines.append(5)", LOREM))
    #
    #     self.assertListEqual(['http://example.com', 'https://example.org', 'http://nic.cz'],
    #                          self.go(r"lines.extend(search(r'(https?://[^\s]+)', line).groups())", LOREM))

    def test_text(self):
        """ Access to the `text` variable in the main clause depends on the `--whole` flag. """
        # Single line processed. Access to `text` variable.
        self.go(r"len(text)", LOREM, custom_cmd="-1w", expect=["209"])

        # All line processed. Access to `text` variable.
        self.go(r"len(text)", LOREM, custom_cmd="-w", expect=["209"] * 4)

        # No access to `text` variable. (Not fetched, should produce an invisible exception.)
        self.go(r"len(text)", LOREM, expect=[forgotten_text] + [exc_text + v for v in LOREM.splitlines()])
        self.go(r"len(text)", LOREM, expect=[], quiet=True)

    def test_skip(self):
        """ Variable can be skipped """
        self.go("skip = s in c; c.add(s);", "1\n2\n2\n3", setup="c=set();", expect=["1", "2", "3"])

    def test_using_regex(self):
        """ Re methods are imported. We try to extract all URLs in a text. """

        # Find all URLs
        self.assertListEqual(['http://example.com', 'http://csirt.cz', 'https://example.org',
                              'http://nic.cz', 'http://example.com'],
                             self.go(r"findall(r'(https?://[^\s]+)', s)", LOREM))

        # search first URL on a line
        self.assertListEqual(['http://example.com', 'https://example.org', 'http://nic.cz'],
                             self.go(r"search(r'(https?://[^\s]+)', s)[0]", LOREM, stderr=DEVNULL))

        # Pass line if it begins with an URL
        self.assertListEqual(['https://example.org'],
                             self.go(r"match(r'(https?://[^\s]+)', s)[0]", LOREM, stderr=DEVNULL))

    def test_number(self):
        self.go("n+5", "1", expect=6)
        self.go("s+5", "1", expect=[], quiet=True)

    def test_set(self):
        self.go("S.add(s)", "2\n1\n2\n3\n1", end="sorted(S)", expect=["1", "2", "3"])

    def test_counter(self):
        # unique letters
        self.go("C.update(s)", "one two\nthree four two one", end="len(C)", expect=10)
        # unique words
        self.go("C.update(s.split())", "one two\nthree four two one", end="len(C)", expect=4)
        # most common
        self.go("C.update(s.split())", "one two\nthree four two one", end="C.most_common",
                expect=["one, 2", "two, 2", "three, 1", "four, 1"])

    def test_generator(self):
        self.go("n", generate="2", expect=["1", "2"])
        self.go("n+2", generate="", expect=["3", "4", "5", "6", "7"])
        self.go("factorial", generate="", expect=["1", "2", "6", "24", "120"])


class TestReturnValues(TestMaster):
    """ Correct command prepending etc. """

    def go_csv(self, command):
        ret = self.go(command, CSV)
        self.assertEqual(10, len(ret))
        return ret

    def test_single_line_without_assignment(self):
        """ `s = ` is prepended when not present"""
        self.assertEqual("Jamaica", self.go_csv(self.col2)[0])

    def test_single_line_with_assignment(self):
        """ `s = ` is not prepended, assignement is already present """
        self.assertEqual("Jamaica", self.go_csv('s = ' + self.col2)[0])

    def test_keyword_without_assignment(self):
        """ The command does not contain an assignment, however it starts with a keyword.
            It would hence be a complex task to put there an assignment automatically.
        """
        # the command clause cannot be internally changed to `s = if ...`
        self.go("if n > 1: L.append(s)", "2\n1\n2\n3\n1", end="len(L)", custom_cmd="-0", expect="3")

    def test_comparing(self):
        """ `s = ` is prepended, we do not get confused if '==' has already been present """
        self.assertEqual(['True'], self.go(self.col2 + ' == "Jamaica"', CSV))

    def test_wrong_command(self):
        """ the command is wrong and does nothing since there are both '=' and ';', the line will not change """
        self.assertListEqual(CSV.splitlines(), self.go_csv('a=1;' + self.col2))

    def test_callable(self):
        num = "1\n2\n3\n4"
        # modified to `s.lower(original_line)`
        self.go("s.lower", "ABcD", expect="abcd")
        # modified int `n` to `sqrt(n)`
        self.go("sqrt", "25", expect=5.0)
        # modified float `n` to `sqrt(n)`
        self.go("round", "5.0", expect=5)

        self.go("sum", num, expect=[], quiet=True, custom_cmd="--overflow-safe")

        self.go("sum", num, expect=["1", "3", "6", "10"])

        self.go("", num, end="sum", expect="10")
        self.go("sum", num, end="sum", expect=["1", "3", "6", "10", "10"])
        self.go("n", num, end="sum", expect=["1", "2", "3", "4", "10"])
        self.go("1", num, end="sum", expect=["1", "1", "1", "1", "10"])
        self.go("", num, end="' - '.join", expect=["1 - 2 - 3 - 4"])

    def test_callable_with_no_output(self):
        """ When treating callable, we have to be able to put the line as its parameter.
            However, we have to distinguish the cases when there is an output (should be displayed)
            and there is no output (we must not print `None` unless --empty is set).
        """
        self.go("S.add", "1\n2\n2\n3", end="sorted(S)", expect=["1", "2", "3"])
        self.go("S.add(s)", "1\n2\n2\n3", end="sorted(S)", expect=["1", "2", "3"])
        self.go("S.add(s);s", "1\n2\n2\n3", end="sorted(S)", expect=["1", "2", "2", "3", "1", "2", "3"])
        self.go("S.add", "1\n2\n2\n3", empty=True, end="sorted(S)", expect=[*["None"] * 4, "1", "2", "3"])

    def test_iterable(self):
        self.go("[1,2,3]", "hi", expect=["1", "2", "3"])

    def test_tuple(self):
        self.go("(1,2,3)", "hi", expect="1, 2, 3")

    def test_match_output(self):
        """ When outputting a regular expression, we use its groups or the matched portion of the string"""

        self.go(r"\s.*", "hello world", custom_cmd="--search", expect=" world")
        self.go(r'search(r"\s.*", s)', "hello world", expect=" world")

        self.go(r"\s(.*)", "hello world", custom_cmd="--search", expect="world")
        self.go(r'search(r"\s(.*)", s)', "hello world", expect="world")

        self.go(r"(.*)\s(.*)", "hello world", custom_cmd="--search", expect="hello, world")
        self.go(r'search(r"(.*)\s(.*)", s)', "hello world", expect="hello, world")

        # outputs the group 1
        self.go('search(r"""([^1])""", s)', "1a\n2b\n3c", expect=["a", "2", "3"])

        # outputs the group 0
        self.go('search(r"""[^a]*""", s)', "1a\n2b\n3c", expect=["1", "2b", "3c"])

        # outputs the group 0
        self.go('match(r"""[^1]*""", s)', "1a\n2b\n3c", expect=["2b", "3c"])

        # take the second char from the string that does not start with a '1'
        # outputs the group 1
        self.go('match(r"""[^1](.*)""", s)', "1a\n2b\n3c", expect=["b", "c"])

    def test_triple_quotes(self):
        """ you can use triple quotes inside a string """
        self.go(r'match(r"""[^"]*"(.*)".""", s)', """hello "world".""", expect=["world"])

    def test_regular_commands(self):
        """ You can use ex: --match instead of `s = match(..., s)` """
        self.go(r"(.*)\s(.*)", "hello world\nanother words", custom_cmd="--match",
                expect=["hello, world", "another, words"])

        self.go(r"([^\s]*)", "hello world\nanother words", custom_cmd="--match", expect=["hello", "another"])
        self.go(r"([^\s]*)", "hello world\nanother words", custom_cmd="--findall",
                expect=["hello", "world", "another", "words"])

    def test_regular_command_sub(self):
        self.go(r"[ae]", "hello world\nanother words", sub=r":", expect=["h:llo world", ":noth:r words"])

        # using groups
        self.go(r"[ae](.)", "hello world\nanother words", sub=r"\1-", expect=["hl-lo world", "n-othr- words"])

    def test_output_tuples_in_list(self):
        """ If we encounter a list of tuples, we properly joins tuples on independents lines. """
        # The bad thing would be to print out this (see the parenthesis)
        # (hello, world)
        # (another, words)
        self.go(r"(.*)\s(.*)", "hello world\nanother words", custom_cmd="--findall",
                expect=["hello, world", "another, words"])

    def test_bytes(self):
        """ Raw output possible (not in the Python format b'string')
        When enriching a callable with a byte-encoded parameter "b64encode" += "(s.encode('utf-8')" instead of "(s)"
        """
        s = "hello world\nanother words"
        self.go("b64encode(s.encode('utf-8'))", s, expect=["aGVsbG8gd29ybGQ=", "YW5vdGhlciB3b3Jkcw=="])
        self.go("b64encode", s, expect=["aGVsbG8gd29ybGQ=", "YW5vdGhlciB3b3Jkcw=="])
        self.go("b64encode", '\x66\x6f\x6f', expect="Zm9v")
        self.go("b64encode", "HEllO", expect="SEVsbE8=")
        self.go("b64encode(bytes(s, 'utf-8'))", "HEllO", expect="SEVsbE8=")


class TestUsecases(TestMaster):
    def test_random_number(self):
        self.assertTrue(0 < int(self.go(r'randint(1,10)', CSV)[0]) < 11)

    def test_csv_reader(self):
        self.go("(x[1] for x in csv.reader([s]))", piped_text='"one","two, still two",three', expect="two, still two")

    def test_multiline_statement(self):
        self.go('''if n > 2:
  s = 'bigger'
else:
  s = 'smaller'
''', piped_text="1\n2\n3", expect=["smaller", "smaller", "bigger"])


if __name__ == '__main__':
    unittest.main()
