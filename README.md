# pyed
[![Build Status](https://travis-ci.org/CZ-NIC/pyed.svg?branch=main)](https://travis-ci.org/CZ-NIC/pyed)

Ever wished to use Python in Bash? Would you choose the Python syntax over `sed`, `awk`, ...? Should you exactly now what command would you use in Python but you end up querying `man` again and again, read further. Pipe the contents in and let `pyed` to process it through your tiny Python script.

How? Simply meddle with the `s` variable. Example: appending '.com' to every line.
```bash
$ echo -e "example\nwikipedia" | pyed 's += ".com"'
example.com
wikipedia.com
```

- [Installation](#installation)
- [Examples](#examples)
- [Docs](#docs)
  * [Scope variables](#scope-variables)
  * [Auto-import](#auto-import)
  * [Output](#output)
  * [CLI flags](#cli-flags)
    * [Regular flags](#regular-flags)

# Installation
Install with a single command from [PyPi](https://pypi.org/project/pyed/).
```bash 
pip3 install pyed    
```

Or download and launch the [`pyed`](https://raw.githubusercontent.com/CZ-NIC/pyed/main/pyed) file from here.

# Examples

How does your data look when `pyed`? Which Bash programs may the utility substitute?

## Extract a substring

Just use the `[:]` notation.

```
bash
echo "hello world" | pyed s[6:]  # hello
```

## Prepend to every line in a stream

We prepend the length of the line.

```bash
tail -f /var/log/syslog | pyed 'f"{len(s)}: {s}"'
```

## Converting to uppercase

Replacing `| tr '[:upper:]' '[:lower:]'`.

```bash
echo "HELLO" | pyed s.lower  # "hello"
```
## Parsing numbers

Replacing `cut`. Note you can chain multiple `pyed` calls. Split by comma '`,`', then use `n` to access the line converted to a number. 
```bash
echo "hello,5" | pyed 's.split(",")[1]' | pyed n+7  # 12
```

## Find out all URLs in a text

Replacing `sed`. We know that all functions from the `re` library are already included, ex: "findall".

```bash
# either use the `--findall` flag
pyed --findall "(https?://[^\s]+)" < file.log

# or expand the full command to which is the `--findall` flag equivalent
pyed "findall(r'(https?://[^\s]+)', s)" < file.log
```

If chained, you can open all the URLs in the current web browser. Note that the function `webbrowser.open` gets auto-imported from the standard library.
```bash
pyed --findall "(https?://[^\s]+)" < file.log | pyed webbrowser.open
```

## Sum numbers
Replacing `| awk '{count+=$1} END{print count}'` or `| paste -sd+ | bc`. Just use `sum` in the `--finally` clause.

```bash
echo -e "1\n2\n3\n4" | pyed --finally sum  # 10
```

## Keep unique lines

Replacing `| sort | uniq` makes little sense but the demonstration gives you the idea. We initialize a set `c` (like a *collection*). When processing a line, `skip` is set to `True` if already seen.  

```bash
$ echo -e "1\n2\n2\n3" | pyed "skip = s in c; c.add(s)"  --setup "c=set()"
1
2
3
``` 

However, an advantage over `| sort | uniq` comes when handling a stream. You see unique lines instantly, without waiting a stream to finish. Useful when using with `tail --follow`.

Alternatively, to assure the values are sorted, we can make a use of `--finally` flag that produces the output after the processing finished. 
```bash
echo -e "1\n2\n2\n3" | pyed "Set.add(s)" --finally "sorted(Set)"  -0
```
Note that we used the variable `Set` which is initialized by default to an empty set (hence we do not have to use `--setup` at all) and the flag `-0` to prevent the processing from output (we do not have to use `skip` parameter then).

<sub>(Strictly speaking we could omit `-0` too. If you use the most verbose `-vvv` flag, you would see the command changed to `s = Set.add(s)` internally. And since `set.add` produces `None` output, it is the same as if it was skipped.)</sub> 

## Handling nested quotes
To match every line that has a quoted expressions and print out the quoted contents, you may serve yourself of Python triple quotes. In the example below, an apostrophe is used to delimite the `COMMAND` flag. If we used an apostrophe in the text, we had have to slash it. Instead, triple quotes might improve readability.
```bash
echo -e 'hello "world".' | pyed 'match(r"""[^"]*"(.*)".""", s)' # world
```

In that case, even better is to use the `--match` flag to get rid of the quoting as much as possible.
```bash
echo -e 'hello "world".' | pyed --match '[^"]*"(.*)"'  # world
``` 

# Docs

## Scope variables

In the script scope, you have access to the following variables:
* `s`: Current line, change it according to your needs
    ```bash
    echo 5 | pyed 's += "4"'  # 54 
    ```
* `n`: Current line converted to an `int` (or `float`) if possible
    ```bash
    echo 5 | pyed n+2  # 7
    echo 5.2 | pyed n+2  # 7.2
    ```
* `text`: Whole text, all lines together (available only with the `--whole` flag set)  
    Ex: get character count (an alternative to `| wc -c`).
    ```
    echo -e "hello\nworld" | pyed --finally 'len(text)' --whole  # 12
    ```
* `lines`: List of lines so far processed (available only with the `--lines` flag set)  
    Ex: returning the last line
    ```bash
    # the `--lines` flag is automatically on when `--finally` used
    echo -e "hello\nworld" | pyed --finally lines[-1]  # "world"
    ```
* `numbers`: List of numbers so far processed (available only with the `--lines` flag set)  
    Ex: show current average of the stream. More specifically, we print out tuples: `line count, current line, average`.
    ```bash
    $ echo -e "20\n40\n25\n28" | pyed 'i+=1; s = i, s, sum(numbers)/i' --lines
    1, 20, 20.0
    2, 40, 30.0
    3, 25, 28.333333333333332
    4, 28, 28.25
    ```
* `skip`: If set to `True`, current line will not be output. If set to `False` when using the `-0` flag, the line will be output regardless. 
* Other variables are initialized and ready to be used globally. They are common for all the lines.
    * `i = 0`
    * `set_ = Set = set()`
    * `list_ = List = list()`
    * `dict_ = Dict = dict()`
    ```bash
    echo -e "2\n1\n2\n3\n1" | pyed "Set.add(s)" --end "sorted(Set)"
    1
    2
    3  
    ``` 
  
    It is true that using uppercase is against naming convention. However in these tiny scripts the readability is the chief principle, every character counts. It is then up to you to decide using either `set_` or `Set`.

## Auto-import

* You can always import libraries you need manually. (Put `import` statement into the command.)
* Some libraries are ready to be used: `re.* (match, search, findall), math.* (sqrt,...), datetime.* (datetime.now, ...), defaultdict`
* Some others are auto-imported whenever its use has been detected. In such case, the line is reprocessed.
    * Functions: `(pathlib).Path, (time).sleep, (random).randint, (requests).get`
    * Modules: `pathlib, time, jsonpickle, requests, humanize`

Caveat: When accessed first time, the auto-import makes the row reprocessed. It may influence your global variables. Use verbose output to see if something has been auto-imported. 
```bash
echo -e "hey\nbuddy" | pyed 'a+=1; sleep(1); b+=1; s = a,b ' --setup "a=0;b=0;" -vv
Importing sleep from time
2, 1
3, 2
```
As seen, `a` was incremented 3× times and `b` on twice because we had to process the first line twice in order to auto-import sleep. In the first run, the processing raised an exception because `sleep` was not known. To prevent that, explicitly appending `from time import sleep` to the `--setup` flag would do. 



## Output
* Explicit assignment: By default, we output the `s`.
    ```bash
    echo "5" | pyed 's = len(s)' # 1
    ```
* Single expression: If not set explicitly, we assign the expression to `s` automatically.
    ```bash
    echo "5" | pyed 'len(s)'  # 1 (command internally changed to `s = len(s)`)
    ```
* Tuple, generator: If `s` ends up as a tuple, its get joined by spaces.
    ```bash
    $ echo "5" | pyed 's, len(s)'
    5, 1 
    ```
  
    Consider piping two lines 'hey' and 'buddy'. We return three elements, original text, reversed text and its length.
    ```bash
    $ echo -e "hey\nbuddy" | pyed 's,s[::-1],len(s)' 
    hey, yeh, 3
    buddy, yddub, 5
    ```
* List: When `s` ends up as a list, its elements are printed to independent lines.
    ```bash
    $ echo "5" | pyed '[s, len(s)]'
    5
    1 
    ```
* Regular match: All groups are treated as a tuple. If no group used, we print the entire matched string.
    ```bash
    # no group → print entire matched string
    echo "hello world" | pyed 'search(r"\s.*", s)' # " world"
  
    # single matched group
    echo "hello world" | pyed 'search(r"\s(.*)", s)' # "world"
  
    # matched groups treated as tuple
    echo "hello world" | pyed 'search(r"(.*)\s(.*)", s)'  # "hello, world"
    ```
* Callable: It gets called. Very useful when handling simple function – without the need of explicitly putting parenthesis to call the function, we can omit quoting in Bash (expression `s.lower()` would have had to be quoted.) Use 3 verbose flags `-vvv` to inspect the internal change of the command.
    ```bash
    # internally changed to `s = s.lower()`
    echo "HEllO" | pyed s.lower  # "hello"
      
    # internally changed to `s = len(s)`
    echo "HEllO" | pyed len  # "5"
  
    # internally changed to `s = base64.b64encode(s.encode('utf-8'))`
    echo "HEllO" | pyed b64encode  # "SEVsbE8="
  
    # internally changed to `s = math.sqrt(n)`
    # and then to `s = round(n)`
    echo "25" | pyed sqrt | pyed round  # "5"
  
    # internally changed to `s = sum(numbers)`
    # `numbers` are available only when `--lines` or `--finally` set
    echo -e "1\n2\n3\n4" | pyed sum --lines
    1
    3
    6
    10
  
    # internally changed to `' - '.join(lines)`
    # `lines` are available only when `--lines` or `--finally` set  
    echo -e "1\n2\n3\n4" | pyed  --finally "' - '.join"
    1 - 2 - 3 - 4
    ```
  
  As you see in the examples, if `TypeError` raised, we try to reprocess the row while adding current line as the argument: 
    * either its basic form `s`
    * the `numbers` if available
    * using its numeral representation `n` if available
    * encoded to bytes `s.encode('utf-8')`
    
  In the `--finally` clause, we try furthermore the `lines`.  

## CLI flags
* `command`: Any Python script (multiple statements allowed)
* `--setup`: Any Python script, executed before processing. Useful for variable initializing.
    Ex: prepend line numbers by incrementing a variable `count`.
    ```bash
    $ echo -e "row\nanother row" | pyed 'count+=1;s = f"{count}: {s}"'  --setup 'count=0'
    1: row
    2: another row
    ```
    <sub>Yes, we could use globally initialized variable `i` instead of using `--setup`.</sub>
* `--finally`: Any Python script, executed after processing. Useful for final output.
    Turns on the `--lines` automatically because we do not expect an infinite stream.
    ```bash
    $ echo -e "1\n2\n3\n4" | pyed --finally sum
    10
    $ echo -e "1\n2\n3\n4" | pyed s --finally sum
    1
    2
    3
    4
    10  
    $ echo -e "1\n2\n3\n4" | pyed sum --finally sum
    1
    3
    6
    10
    10
    ```
* `--verbose`: If you end up with no output, turn on to see what happened. Used once: show command exceptions. Twice: show automatic imports. Thrice: see internal command modification (attempts to make it callable and prepending `s =` if omitted).  
    ```bash
    $ echo -e "hello" | pyed 'invalid command' # empty result
    $ echo -e "hello" | pyed 'invalid command' -v
    Exception: <class 'SyntaxError'> invalid syntax (<string>, line 1) on line: hello
    $ echo -e "hello" | pyed 'sleep(1)' -vv
    Importing sleep from time
    ```
* `--filter`: Line is piped out unchanged, however only if evaluated to `True`.
    When piping in numbers to 5, we pass only such bigger than 3.
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pyed "n > 3"  --filter
    4
    5
    ```
    The statement is equivalent to using `skip` (and not using `--filter`).
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pyed "skip = not n > 3"
    4
    5
    ```
    When not using filter, `s` evaluates to `True` / `False`. By default, `False` or empty values are not output. 
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pyed "n > 3"   
    True
    True
    ```
* `n`: Process only such number of lines. Roughly equivalent to `head -n`.
* `-1`: Process just the first line. Useful in combination with `--whole`.
* `--whole`: Fetch the whole text first before processing. Variable `text` is available containing whole text. You might want to add `-1` flag.
    ```bash
    $ echo -e "1\n2\n3" | pyed 'len(text)' 
    Did not you forget to use --whole?
    ```
  
    Appending `--whole` helps but the result is processed for every line again.
    ```bash
    $ echo -e "1\n2\n3" | pyed 'len(text)' -w 
    6
    6
    6
    ```
  
    Appending `-1` makes sure the statement gets computed only once. 
    ```bash
    $ echo -e "1\n2\n3" | pyed 'len(text)' -w1
    6    
    ```
* `--lines`: Populate `lines` and `numbers` with lines. This is off by default since this would cause an overflow when handling an infinite input.
    ```bash
    $ echo -e "1\n2\n3\n4" | pyed sum  --lines  # (internally changed to `s = sum(numbers)`
    1
    3
    6
    10      
    ```
* `--empty` Output even empty lines. (By default skipped.)  
    Consider shortening the text by 3 last letters. First line `hey` disappears completely then.
    ```bash
    $ echo -e "hey\nbuddy" | pyed 's[:-3]'
    bu
    ```
    Should we insist on displaying, we see an empty line now.
    ```bash
    $ echo -e "hey\nbuddy" | pyed 's[:-3]' --empty
    
    bu
    ```
* `-0`: Skip all lines output. (Useful in combination with `--finally`.)

### Regular flags
* `--search`: Equivalent to `search(COMMAND, s)`
    ```bash
    $ echo -e "hello world\nanother words" | pyed --search ".*\s"
    hello
    another
    ```
* `--match`: Equivalent to `match(COMMAND, s)`
* `--findall`: Equivalent to `findall(COMMAND, s)`
* `--sub SUBSTITUTION`: Equivalent to `sub(COMMAND, SUBSTITUTION, s)`
    ```bash
    $ echo -e "hello world\nanother words" | pyed --sub ":" ".*\s"
    :world
    :words
    ```
    
    Using groups
    ```bash
    $ echo -e "hello world\nanother words" | pyed --sub "\1" "(.*)\s"
    helloworld
    anotherwords
    ```
