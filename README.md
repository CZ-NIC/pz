# pz
[![Build Status](https://travis-ci.org/CZ-NIC/pz.svg?branch=main)](https://travis-ci.org/CZ-NIC/pz)
[![Downloads](https://pepy.tech/badge/pz)](https://pepy.tech/project/pz)

Ever wished to use Python in Bash? Would you choose the Python syntax over `sed`, `awk`, ...? Should you exactly know what command would you use in Python, but you end up querying `man` again and again, read further. The utility allows you to *pythonize* the shell: to pipe arbitrary contents through `pz`, loaded with your tiny Python script.

**How? Simply meddle with the `s` variable.** Example: appending '.com' to every line.
```bash
$ echo -e "example\nwikipedia" | pz 's += ".com"'
example.com
wikipedia.com
```

- [Installation](#installation)
- [Examples](#examples)
  * [Extract a substring](#extract-a-substring)
  * [Prepend to every line in a stream](#prepend-to-every-line-in-a-stream)
  * [Converting to uppercase](#converting-to-uppercase)
  * [Parsing numbers](#parsing-numbers)
  * [Find out all URLs in a text](#find-out-all-urls-in-a-text)
  * [Sum numbers](#sum-numbers)
  * [Keep unique lines](#keep-unique-lines)
  * [Counting words](#counting-words)
  * [Fetching web content](#fetching-web-content)
  * [Handling nested quotes](#handling-nested-quotes)
  * [Computing factorial](#computing-factorial)
  * [Read CSV](#read-csv)
  * [Generate random number](#generate-random-number)
  * [Average a stream value](#average-a-stream-value)
  * [Multiline statements](#multiline-statements)
  * [Simple progress bar](#simple-progress-bar)
- [Docs](#docs)
  * [Scope variables](#scope-variables)
    + [`s` – current line](#s--current-line)
    + [`n` – current line converted to an `int` (or `float`) if possible](#n--current-line-converted-to-an-int-or-float-if-possible)
    + [`b` – current line as a byte-string](#b--current-line-as-a-byte-string)
    + [`count` – current line number](#count--current-line-number)
    + [`text` – whole text, all lines together](#text--whole-text-all-lines-together)
    + [`lines` – list of lines so far processed](#lines--list-of-lines-so-far-processed)
    + [`numbers` – list of numbers so far processed](#numbers--list-of-numbers-so-far-processed)
    + [`skip` line](#skip-line)
    + [`i`, `S`, `L`, `D`, `C` – other global variables](#i-s-l-d-c--other-global-variables)
  * [Auto-import](#auto-import)
  * [Output](#output)
  * [CLI flags](#cli-flags)
    + [Command clauses](#command-clauses)
    + [Input / output](#input--output)
    + [Regular expressions shortcuts](#regular-expressions-shortcuts)
    + [Bash completion](#bash-completion)

# Installation
Install with a single command from [PyPi](https://pypi.org/project/pz/).
```bash 
pip3 install pz    
```

Or download and launch the [`pz`](https://raw.githubusercontent.com/CZ-NIC/pz/main/pz) file from here.

# Examples

How does your data look when pythonized via `pz`? Which Bash programs may the utility substitute?

## Extract a substring

Just use the `[:]` notation.

```bash
echo "hello world" | pz s[6:]  # hello
```

## Prepend to every line in a stream

We prepend the length of the line.

```bash
# let's use the f-string `--format` flag
tail -f /var/log/syslog | pz -f '{len(s)}: {s}' 

# or do it the long way, explicitly setting the `s` variable
tail -f /var/log/syslog | pz 's = str(len(s)) + ": " + s'
```

## Converting to uppercase

Replacing `| tr '[:upper:]' '[:lower:]'`.

```bash
echo "HELLO" | pz s.lower  # "hello"
```
## Parsing numbers

Replacing `cut`. Note you can chain multiple `pz` calls. Split by a comma '`,`', then use `n` to access the line converted to a number. 
```bash
echo "hello,5" | pz 's.split(",")[1]' | pz n+7  # 12
```

## Find out all URLs in a text

Replacing `sed`. We know that all functions from the `re` library are already included, ex: "findall".

```bash
# either use the `--findall` flag
pz --findall "(https?://[^\s]+)" < file.log

# or expand the full command to which is the `--findall` flag equivalent
pz "findall(r'(https?://[^\s]+)', s)" < file.log
```

If chained, you can open all the URLs in the current web browser. Note that the function `webbrowser.open` gets auto-imported from the standard library.
```bash
pz --findall "(https?://[^\s]+)" < file.log | pz webbrowser.open
```

## Sum numbers
Replacing `| awk '{count+=$1} END{print count}'` or `| paste -sd+ | bc`. Just use `sum` in the `--end` clause.

```bash
# internally changed to --end `s = sum(numbers)`
echo -e "1\n2\n3\n4" | pz --end sum  # 10
```

## Keep unique lines

Replacing `| sort | uniq` makes little sense, but the demonstration gives you the idea. We initialize a set `c` (like a *collection*). When processing a line, `skip` is set to `True` if already seen.  

```bash
$ echo -e "1\n2\n2\n3" | pz "skip = s in c; c.add(s)"  --setup "c=set()"
1
2
3
``` 

However, an advantage over `| sort | uniq` comes when handling a stream. You see unique lines instantly, without waiting a stream to finish. Useful when using with `tail --follow`.

Alternatively, to assure the values are sorted, we can make a use of `--end` flag that produces the output after the processing finished.
```bash
echo -e "1\n2\n2\n3" | pz "S.add(s)" --end "sorted(S)" -0
```

Note that we used the variable `S` which is initialized by default to an empty set (hence we do not have to use `--setup` at all) and the flag `-0` to prevent the processing from output (we do not have to use `skip` parameter then).

<sub>(Strictly speaking we could omit `-0` too. If you use the verbose `-v` flag, you would see the command changed to `s = S.add(s)` internally. And since `set.add` produces `None` output, it is the same as if it was skipped.)</sub>

We can omit `(s)` in the `main` clause and hence get rid of the quotes all together.
```bash
echo -e "1\n2\n2\n3" | pz S.add --end "sorted(S)"
```

Nevertheless, the most straightforward approach would involve the `lines` variable, available when using the `--end` clause.

```bash
echo -e "1\n2\n2\n3" | pz --end "sorted(set(lines))"
``` 

## Counting words

We split the line to get the words and put them in `S`, a global instance of the `set`. Then, we print the set length to get the number of unique words.

```bash
echo -e "red green\nblue red green" | pz 'S.update(s.split())' --end 'len(S)'  # 3
```

But what if we want to get the most common words and the count of its usages? Let's use `C`, a global instance of the `collections.Counter`. We see then the `red` is the most_common word and has been used 2 times.
```bash
$ echo -e "red green\nblue red green" | pz 'C.update(s.split())' --end C.most_common
red, 2
green, 2
blue, 1
```

## Fetching web content

Accessing internet is easy thanks to the [`requests`](https://requests.readthedocs.io/en/master/) library. Here, we fetch `example.com`, grep it for all lines containing "href" and print them out while stripping spaces.

```bash
$ echo "http://example.com" | pz 'requests.get(s).content' | grep href | pz s.strip 
<p><a href="https://www.iana.org/domains/example">More information...</a></p>
```

To see how auto-import are resolved, use the verbose mode. (Notice the line `Importing requests`.)
```bash
$ echo "http://example.com" | pz 'requests.get(s).content' -v | grep href | pz s.strip 
Changing the command clause to: s = requests.get(s).content
Importing requests
<p><a href="https://www.iana.org/domains/example">More information...</a></p>
```


## Handling nested quotes
To match every line that has a quoted expressions and print out the quoted contents, you may serve yourself of Python triple quotes. In the example below, an apostrophe is used to delimit the `COMMAND` flag. If we used an apostrophe in the text, we would have to slash it. Instead, triple quotes might improve readability.
```bash
echo -e 'hello "world".' | pz 'match(r"""[^"]*"(.*)".""", s)' # world
```

In that case, even better is to use the `--match` flag to get rid of the quoting as much as possible.
```bash
echo -e 'hello "world".' | pz --match '[^"]*"(.*)"'  # world
``` 

## Computing factorial

Take a look at multiple ways. The simplest is to use the function.

```bash
echo 5 | pz factorial  # 120
```

What happens in the background? `factorial` is available from `math.factorial`. Since it is a callable, we try to put current line as the parameter: `factorial(s)`. Since `s = "5"` which means a string, it fails. It then tries to use `factorial(n)` where `n` is current line automatically fetched to a number. That works.

Harder way? Let's use `math.prod` then.

```bash
echo 5 | pz 'prod(i for i in range(1,n+1))'  # 120
```

Without any built-in library? Let's just use a for-cycle. Process all numbers from 1 to `n` (which is 5) and multiply to product. Finally, assign `n` to `s` which is output.

```bash
echo 5 | pz 'for c in range(1,n): n*= c ; s = n'   # 120
```

Using generator will print a factorial for every number from 1 to `-g`.

```bash
$ pz factorial -g5
1
2
6
24
120
```

## Read CSV

As `csv` is one of the auto-imported libraries, we may directly access instantiate the reader object. In the following example, we output the second element of every line either progressively or at once when processing finished. 

```bash
# output line by line
echo '"a","b1,b2,b3","c"' | pz "(x[1] for x in csv.reader([s]))"  # "b1,b2,b3"

# output at the end
echo '"a","b1,b2,b3","c"' | pz --end "(x[1] for x in csv.reader(lines))"  # "b1,b2,b3"   
````

## Generate random number

First, take a look how to stream random numbers to 100 in Bash.

```bash
while :; do echo $((1+$RANDOM%100)); done
```

Now examine pure Python solution, without having `pz` involved.

```bash
python3 -c "while True: from random import randint; print(randint(1,100))"
```

Using `pz`, we relieve the cycle handling and importing burden from the command.

```bash
pz "randint(1,100)" --generate=0
```

Let's generate few random strings of variable length 1 to 30. When generator flag is used without a number, it cycles five times.
```bash
pz "''.join(random.choice(string.ascii_letters) for _ in range(randint(1,30)))" -S "import string" -g
``` 

## Average a stream value

Let's have a stream and output the average value.

```bash
# print out current line `count` and current average `sum/count`
$ while :; do echo $((1 + $RANDOM % 100)) ; sleep 0.1; done | pz 'sum+=n;s=count, sum/count' --setup "sum=0"
1, 38.0
2, 67.0
3, 62.0
4, 49.75

# print out every 10 000 lines
# (thanks to `not i % 10000` expression) 
$ while :; do echo $((1 + $RANDOM % 100)) ;  done | pz 'sum+=n;s=sum/count; s = (count,s) if not count % 10000 else ""' --setup "sum=0"
10000, 50.9058
20000, 50.7344
30000, 50.693466666666666
40000, 50.5904
```

How can this be simplified? Let's use an infinite generator `-g0`. As we know, `n` is given current line number by the generator and `i` is by default implicitly declared to `i=0` so we use it to hold the sum. No setup clause needed. No Bash cycle needed. 
```bash
$ pz "i+=randint(1,100); s = (n,i/n) if not n % 10000 else ''" -g0
10000, 49.9488
20000, 50.5399
30000, 50.39906666666667
40000, 50.494425
```

## Multiline statements

Should you need to evaluate a short multiline statement, use standard multiline statements, supported by Bash.

```bash
$ echo -e "1\n2\n3" | pz "if n > 2:
  s = 'bigger'
else:
  s = 'smaller'
"
smaller
bigger
bigger
```

## Simple progress bar

Simulate a lengthy processing by generating a long sequence of numbers (as they are not needed, we throw them away by `1>/dev/null`).
On every 100th line, we move cursor up (`\033[1A`), clear line (`\033[K`) and print to `STDERR` current status.  

```bash
$ seq 1 100000 | pz 's = f"\033[1A\033[K ... {count} ..." if count % 100 == 0 else None ' --stderr 1>/dev/null
 ... 100 ...  # replaced by ... 200 ...
```

# Docs

## Scope variables

In the script scope, you have access to the following variables:

### `s` – current line
Change it according to your needs
```bash
echo 5 | pz 's += "4"'  # 54 
```

### `n` – current line converted to an `int` (or `float`) if possible
```bash
echo 5 | pz n+2  # 7
echo 5.2 | pz n+2  # 7.2
```

### `b` – current line as a byte-string
Sometimes the input cannot be converted to str easily. A warning is output, however, you can still operate with raw bytes.
```bash
echo -e '\x80 invalid line' | pz s
Cannot parse line correctly: b'\x80 invalid line'
� invalid line

# use the `--quiet` flag to suppress the warning, then decode the bytes
echo -e '\x80 invalid line' | pz 'b.decode("cp1250")' --quiet
€ invalid line
```

### `count` – current line number
```bash
# display every 1_000nth line
$ pz -g0 n*3 | pz "n if not count % 1000 else None"
3000
6000
9000

# the same, using the `--filter` flag
$ pz -g0 n*3 | pz -F "not count % 1000"
```

### `text` – whole text, all lines together
Not available with the `--overflow-safe` flag set nor in the `main` clause unless the `--whole` flag set.
Ex: get character count (an alternative to `| wc -c`).
```
echo -e "hello\nworld" | pz --end 'len(text)' # 11
```

When used in the `main` clause, an error appears. 
```bash
$ echo -e "1\n2\n3" | pz 'len(text)'
Did not you forget to use --text?
Exception: <class 'NameError'> name 'text' is not defined on line: 1
```

Appending `--whole` helps, but the result is processed for every line.
```bash
$ echo -e "1\n2\n3" | pz 'len(text)' -w 
5
5
5
```

Appending `-1` makes sure the statement gets computed only once. 
```bash
$ echo -e "1\n2\n3" | pz 'len(text)' -w1
5
```

### `lines` – list of lines so far processed
Not available with the `--overflow-safe` flag set.  
Ex: returning the last line
```bash
echo -e "hello\nworld" | pz --end lines[-1]  # "world"
```

### `numbers` – list of numbers so far processed
Not available with the `--overflow-safe` flag set.  
Ex: show current average of the stream. More specifically, we output tuples: `line count, current line, average`.
```bash
$ echo -e "20\n40\n25\n28" | pz 's = count, s, sum(numbers)/count'
1, 20, 20.0
2, 40, 30.0
3, 25, 28.333333333333332
4, 28, 28.25
```

### `skip` line
If set to `True`, current line will not be output. If set to `False` when using the `-0` flag, the line will be output regardless.

### `i`, `S`, `L`, `D`, `C` – other global variables
Some variables are initialized and ready to be used globally. They are common for all the lines.
* `i = 0`
* `S = set()`
* `L = list()`
* `D = dict()`
* `C = Counter()`

<sub>It is true that using uppercase is not conforming the naming convention. However, in these tiny scripts the readability is the chief principle, every character counts.</sub>

Using a set `S`. In the example, we add every line to the set and end print it out in a sorted manner.
```bash
$ echo -e "2\n1\n2\n3\n1" | pz "S.add(s)" --end "sorted(S)"
1
2
3  
``` 

Using a list `L`. Append lines that contains a number bigger than one and finally, print their count. As only the final count matters, suppress the line output with the flag `-0`. 
```bash
$ echo -e "2\n1\n2\n3\n1" | pz "if n > 1: L.append(s)" --end "len(L)" -0
3  
```

## Auto-import

* You can always import libraries you need manually. (Put `import` statement into the command.)
* Some libraries are ready to be used: `re.* (match, search, findall), math.* (sqrt,...), defaultdict`
* Some others are auto-imported whenever its use has been detected. In such case, the line is reprocessed.
    * Functions: `b64decode, b64encode, datetime, (requests).get, glob, iglob, Path, randint, sleep, time, ZipFile`
    * Modules: `base64, collections, csv, humanize, itertools, jsonpickle, pathlib, random, requests, time, webbrowser, zipfile`

Caveat: When accessed first time, the auto-import makes the row reprocessed. It may influence your global variables. Use verbose output to see if something has been auto-imported. 
```bash
$ echo -e "hey\nbuddy" | pz 'a+=1; sleep(1); b+=1; s = a,b ' --setup "a=0;b=0;" -v
Importing sleep from time
2, 1
3, 2
```
As seen, `a` was incremented 3× times and `b` on twice because we had to process the first line twice in order to auto-import sleep. In the first run, the processing raised an exception because `sleep` was not known. To prevent that, explicitly appending `from time import sleep` to the `--setup` flag would do. 



## Output
* Explicit assignment: By default, we output the `s`.
    ```bash
    echo "5" | pz 's = len(s)' # 1
    ```
* Single expression: If not set explicitly, we assign the expression to `s` automatically.
    ```bash
    echo "5" | pz 'len(s)'  # 1 (command internally changed to `s = len(s)`)
    ```
* Tuple, generator: If `s` ends up as a tuple, its get joined by spaces.
    ```bash
    $ echo "5" | pz 's, len(s)'
    5, 1 
    ```
  
    Consider piping two lines 'hey' and 'buddy'. We return three elements, original text, reversed text and its length.
    ```bash
    $ echo -e "hey\nbuddy" | pz 's,s[::-1],len(s)' 
    hey, yeh, 3
    buddy, yddub, 5
    ```
* List: When `s` ends up as a list, its elements are printed to independent lines.
    ```bash
    $ echo "5" | pz '[s, len(s)]'
    5
    1 
    ```
* Regular match: All groups are treated as a tuple. If no group used, we print the entire matched string.
    ```bash
    # no group → print entire matched string
    echo "hello world" | pz 'search(r"\s.*", s)' # " world"
  
    # single matched group
    echo "hello world" | pz 'search(r"\s(.*)", s)' # "world"
  
    # matched groups treated as tuple
    echo "hello world" | pz 'search(r"(.*)\s(.*)", s)'  # "hello, world"
    ```
* Callable: It gets called. Very useful when handling simple function – without the need of explicitly putting parenthesis to call the function, we can omit quoting in Bash (expression `s.lower()` would have had to be quoted.) Use the verbose flag `-v` to inspect the internal change of the command.
    ```bash
    # internally changed to `s = s.lower()`
    echo "HEllO" | pz s.lower  # "hello"
      
    # internally changed to `s = len(s)`
    echo "HEllO" | pz len  # "5"
  
    # internally changed to `s = base64.b64encode(s.encode('utf-8'))`
    echo "HEllO" | pz b64encode  # "SEVsbE8="
  
    # internally changed to `s = math.sqrt(n)`
    # and then to `s = round(n)`
    echo "25" | pz sqrt | pz round  # "5"
  
    # internally changed to `s = sum(numbers)`    
    echo -e "1\n2\n3\n4" | pz sum
    1
    3
    6
    10
  
    # internally changed to `' - '.join(lines)`      
    echo -e "1\n2\n3\n4" | pz  --end "' - '.join"
    1 - 2 - 3 - 4
    ```
  
  As you see in the examples, if `TypeError` raised, we try to reprocess the row while adding current line as the argument: 
    * either its basic form `s`
    * the `numbers` if available
    * using its numeral representation `n` if available
    * encoded to bytes `s.encode('utf-8')`
    
  In the `--end` clause, we try furthermore the `lines`.  

## CLI flags

* `-v`, `--verbose`: See what happens under the hood. Show automatic imports and internal command modification (attempts to make it callable and prepending `s =` if omitted).  
    ```bash
    $ echo -e "hello" | pz 'invalid command'
    Exception: <class 'SyntaxError'> invalid syntax (<string>, line 1) on line: hello
    $ echo -e "hello" | pz 'sleep(1)' --verbose
    Importing sleep from time
    ```
* `-q`, `--quiet`: See errors and values only. Suppress command exceptions.
  ```bash
  echo -e "hello" | pz 'invalid command' --quiet # empty result
  ```
  
### Command clauses
* `COMMAND`: The `main` clause, any Python script executed on every line (multiple statements allowed)
* `-S COMMAND`, `--setup COMMAND`: Any Python script, executed before processing. Useful for variable initializing.
    Ex: prepend line numbers by incrementing a variable `count`.
    ```bash
    $ echo -e "row\nanother row" | pz 'count+=1;s = f"{count}: {s}"'  --setup 'count=0'
    1: row
    2: another row
  
    # the same using globally available variable `count` instead of using `--setup` and the `--format` flag
    $ echo -e "row\nanother row" | pz -f '{count}: {s}'
    ```
* `-E COMMAND`, `--end COMMAND`: Any Python script, executed after processing. Useful for the final output.
    The variable `text` is available by default here.
    ```bash
    $ echo -e "1\n2\n3\n4" | pz --end sum
    10
    $ echo -e "1\n2\n3\n4" | pz s --end sum
    1
    2
    3
    4
    10  
    $ echo -e "1\n2\n3\n4" | pz sum --end sum
    1
    3
    6
    10
    10
    ```
* `-F`, `--filter`: Line is piped out unchanged, however only if evaluated to `True`.
    When piping in numbers to 5, we pass only such bigger than 3.
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pz "n > 3"  --filter
    4
    5
    ```
    The statement is equivalent to using `skip` (and not using `--filter`).
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pz "skip = not n > 3"
    4
    5
    ```
    When not using filter, `s` evaluates to `True` / `False`. By default, `False` or empty values are not output. 
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pz "n > 3"   
    True
    True
    ```
* `-f`, `--format`: Main and end clauses are considered f-strings. The clause is inserted in between three-apostrophes `f'''COMMAND'''` internally.


### Input / output  
* `-n NUM` Process only such number of lines. Roughly equivalent to `head -n`.
* `-1` Process just the first line.
* `-0` Skip all lines output. (Useful in combination with `--end`.)
* `--empty` Output even empty lines. (By default skipped.)  
    Consider shortening the text by 3 last letters. First line `hey` disappears completely then.
    ```bash
    $ echo -e "hey\nbuddy" | pz 's[:-3]'
    bu
    ```
    Should we insist on displaying, we see an empty line now.
    ```bash
    $ echo -e "hey\nbuddy" | pz 's[:-3]' --empty
    
    bu
    ```
* `-g [NUM]`, `--generate [NUM]` Generate lines while ignoring the input pipe. Line will correspond to the iteration cycle count (unless having the `--overflow-safe` flag on while having an infinite generator – in that case, lines will equal to '1'). If `NUM` not specified, 5 lines will be produced by default. Putting `NUM == 0` means an infinite generator. If no `main` clause set, the number is piped out. 
  ```bash
  $ pz -g2
  1
  2
  $ pz 'i=i+5' -g -v
  Changing the main clause to: s = i=i+5
  Generating s = 1 .. 5
  5
  10
  15
  20
  25
  ```
* `--stderr` Print clauses' output to the `STDERR`, while letting the original line piped to `STDOUT` intact. Useful for generating reports during a long operation. Take a look at the following example, every third line will make `STDERR` to receive a message. 
  ```bash
  $ pz -g=9 s | pz "s = 'Processed next few lines' if count % 3 == 0 else None" --stderr 
  1
  2
  3
  Processed next few lines
  4
  5
  6
  Processed next few lines
  7
  8
  9
  Processed next few lines
  ```
  
  Demonstrate different pipes by writing `STDOUT` to a file and leaving `STDERR` in the terminal. 

  ```bash
  $ pz -g=9 s | pz "s = 'Processed next few lines' if count % 3 == 0 else None" --stderr > /tmp/example
  Processed next few lines
  Processed next few lines
  Processed next few lines
  
  cat /tmp/example
  1
  2
  3
  ...  
  ```
* `--overflow-safe` Prevent `lines`, `numbers`, `text` variables to be available. Useful when handling an infinite input.
  ```
  # prevent `text` to be populated by default
  echo -e  "1\n2\n2\n3" | pz --end "len(text)" --overflow-safe
  Did you not forget to use --while to access `text`?
  Exception: <class 'NameError'> name 'text' is not defined in the --end clause
  
  # force to populate `text` 
  echo -e  "1\n2\n2\n3" | pz --end "len(text)" --overflow-safe --whole
  7
  ```

### Regular expressions shortcuts
* `--search` Equivalent to `search(COMMAND, s)`
    ```bash
    $ echo -e "hello world\nanother words" | pz --search ".*\s"
    hello
    another
    ```
* `--match` Equivalent to `match(COMMAND, s)`
* `--findall` Equivalent to `findall(COMMAND, s)`
* `--sub SUBSTITUTION` Equivalent to `sub(COMMAND, SUBSTITUTION, s)`
    ```bash
    $ echo -e "hello world\nanother words" | pz ".*\s" --sub ":"
    :world
    :words
    ```
    
    Using groups
    ```bash
    $ echo -e "hello world\nanother words" | pz "(.*)\s" --sub "\1"
    helloworld
    anotherwords
    ```

### Bash completion
1. Run: `apt-get install bash-completion jq`
2. Copy: [extra/pz-autocompletion.bash](./extra/pz-autocompletion.bash) to `/etc/bash_completion.d/`
3. Restart terminal