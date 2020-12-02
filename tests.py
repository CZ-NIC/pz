import logging
import sys
import unittest
from subprocess import Popen, PIPE, STDOUT

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

forgotten_text = "Did not you forget to use --whole to access `text`?"


class Testpz(unittest.TestCase):
    col2 = 's.split("|")[2]'

    def go(self, command="", piped_text=None, previous_command=None, empty=False, n=None, whole=False, custom_cmd=None,
           expect=None, debug=False, verbosity=0, setup=None, final=None, sub=None):
        cmd = ["./pz"]
        if empty:
            cmd.append("--empty")
        if n:
            cmd.extend(("-n", str(n)))
        if whole:
            cmd.append("--whole")
        if custom_cmd:
            cmd.append(custom_cmd)
        if verbosity:
            cmd.extend(["-v"] * verbosity)
        if setup:
            cmd.extend(["--setup", setup])
        if final:
            cmd.extend(["--finally", final])
        if sub:
            cmd.extend(["--sub", sub])

        if previous_command:
            cmd = previous_command + " | " + " ".join(cmd) + f" '{command}'"
            if debug:
                print("Command", cmd)
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
            stdout, stderr = p.communicate()
        elif piped_text:
            if debug:
                print("Command", cmd + [command])
            p = Popen(cmd + [command], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
            stdout, stderr = p.communicate(input=piped_text.encode("utf-8"))
        else:
            raise AttributeError("Specify either piped_text or previous_command")

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
        # IPC -> sleep in STDIN, sleep in STDOUT XX (ex: tail -f)
        ...


class TestFlags(Testpz):

    def test_number_of_lines(self):
        self.assertEqual(3, len(self.go(self.col2, CSV, n=3)))

    def test_import(self):
        # timedelta should be already present due to `from datetime import *`
        self.go(r's+=str(timedelta(seconds=5))', previous_command="echo '123'", custom_cmd="-vv",
                expect="1230:00:05")

        # when verbosity increased, we should get notified when an import happened
        self.go(r'Path("/")', previous_command="echo '123'", verbosity=0, expect='/')
        self.go(r'Path("/")', previous_command="echo '123'", verbosity=1, expect='/')
        self.go(r'Path("/")', previous_command="echo '123'", verbosity=2, expect=['Importing Path from pathlib', '/'])

    def test_failed_line(self):
        """ Exceptions are shown only if verbosity active. They are correctly printed to STDERR. """

        def check(verbosity=0, expect_stderr=b''):
            p = Popen(["./pz", "invalid line"] + ["-v"] * verbosity,
                      stdout=PIPE, stdin=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate(input=b"1")

            self.assertEqual(b'', stdout)
            self.assertEqual(expect_stderr, stderr)

        exception_text = b"Exception: <class 'SyntaxError'> invalid syntax (<string>, line 1) on line: 1\n"
        check(verbosity=0)
        check(verbosity=1, expect_stderr=exception_text)
        check(verbosity=2, expect_stderr=exception_text)

    def test_debugging(self):
        """ No access to `text` variable. (Not fetched by --whole, should produce an invisible exception.) """
        # verbosity 0
        self.go(r"len(text)", LOREM, expect=forgotten_text, n=1)

        # increased verbosity
        self.go(r"len(text)", LOREM, verbosity=1, n=1,
                expect=[forgotten_text, "Exception: <class 'NameError'> name 'text' is not defined"
                                        " on line: Lorem ipsum dolor sit amet http://example.com"
                                        " consectetur http://csirt.cz"])

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


class TestVariables(Testpz):
    # # deprecated
    # def test_lines(self):
    #     """ Possibility to use `lines` list instead of re-assigning `line`. """
    #     self.assertListEqual(['5'] * 4, self.go(r"lines.append(5)", LOREM))
    #
    #     self.assertListEqual(['http://example.com', 'https://example.org', 'http://nic.cz'],
    #                          self.go(r"lines.extend(search(r'(https?://[^\s]+)', line).groups())", LOREM))

    def test_text(self):
        """ Access to the `list` variable depends on the `--whole` flag. """
        # Single line processed. Access to `text` variable.
        self.go(r"len(text)", LOREM, custom_cmd="-1w", expect=["210"])

        # All line processed. Access to `text` variable.
        self.go(r"len(text)", LOREM, custom_cmd="-w", expect=["210"] * 4)

        # No access to `text` variable. (Not fetched, should produce an invisible exception.)
        self.go(r"len(text)", LOREM, expect=forgotten_text)

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
                             self.go(r"search(r'(https?://[^\s]+)', s)[0]", LOREM))

        # Pass line if it begins with an URL
        self.assertListEqual(['https://example.org'],
                             self.go(r"match(r'(https?://[^\s]+)', s)[0]", LOREM))

    def test_number(self):
        self.go("n+5", "1", expect=6)
        self.go("s+5", "1", expect=[])

    def test_set(self):
        self.go("Set.add(s)", "2\n1\n2\n3\n1", final="sorted(Set)", expect=["1", "2", "3"])


class TestReturnValues(Testpz):
    """ Correct command prepending etc. """

    def go_csv(self, command):
        ret = self.go(command, CSV)
        self.assertEqual(10, len(ret))
        return ret

    def test_single_line_without_assignement(self):
        """ `s = ` is prepended when not present"""
        self.assertEqual("Jamaica", self.go_csv(self.col2)[0])

    def test_single_line_with_assignement(self):
        """ `s = ` is not prepended, assignement is already present """
        self.assertEqual("Jamaica", self.go_csv('s = ' + self.col2)[0])

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

        # since --lines is off, we sum the bytes
        # This is counter-intuitive but I do not want to allow --lines by default
        # since it overflows while processing an infinite input stream.
        # XX self.go("sum", num, expect=["49", "50", "51", "52"])
        self.go("sum", num, expect=[])  # missing --lines

        self.go("sum", num, expect=["1", "3", "6", "10"], custom_cmd="--lines")

        self.go("", num, final="sum", expect="10")
        self.go("sum", num, final="sum", expect=["1", "3", "6", "10", "10"])
        self.go("n", num, final="sum", expect=["1", "2", "3", "4", "10"])
        self.go("1", num, final="sum", expect=["1", "1", "1", "1", "10"])
        self.go("", num, final="' - '.join", expect=["1 - 2 - 3 - 4"])

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


class TestUsecases(Testpz):
    def test_random_number(self):
        self.assertTrue(0 < int(self.go(r'randint(1,10)', CSV)[0]) < 11)


if __name__ == '__main__':
    unittest.main()
