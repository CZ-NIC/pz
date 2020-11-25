# pyed
[![Build Status](https://travis-ci.org/CZ-NIC/pyed.svg?branch=master)](https://travis-ci.org/CZ-NIC/pyed)

Use Python in Bash. Easily handle day to day CLI operation via Python instead of regular Bash programs.  
Should you choose Python syntax over `sed`, `awk` or other tools but you do not want to debug Python interprocess communication, read further. `pyed` will launch your tiny Python script on a piped in contents and pipes it out. 

Example: append '.com' to every line. Simply change the `line` variable.
```bash
$ echo -e "example\nwikipedia" | pyed 'line += ".com"'
example.com
wikipedia.com
```

- [Installation](#installation)
- [Examples](#examples)
- [Docs](#docs)
  * [Scope](#scope)
  * [Auto-import](#auto-import)
  * [Output](#output)
  * [CLI flags](#cli-flags)

# Installation
Install with a single command from [PyPi](https://pypi.org/project/pyed/).
```bash 
pip3 install pyed    
```

# Examples

## Prepend to every line in a stream

We prepend a line count.

```bash
tail -f /var/log/syslog |  pyed 'f"{len(line)}: {line}"'
```

## Find out all URLs in a text

We know that all functions from the `re` library are already included, ex: "findall".

```bash
pyed "findall(r'(https?://[^\s]+)', line)" < file.log
```

## Keep unique lines

Replacing `| sort | uniq` makes little sense but the demonstration gives you the idea. We initialize a set `s`. When processing a line, `skip` is set to `True` when if already seen.  

```bash
$ echo -e "1\n2\n2\n3" | pyed "skip = line in s; s.add(line);"  --setup "s=set();"
1
2
3
``` 

However, an advantage over `| sort | uniq` comes when handling a stream. You see unique lines instantly, without waiting a stream to finish. Useful when using with `tail --follow`.

# Docs

## Scope

In the script scope, you have access to the following variables:
* `line`: current line, you can change it
    ```bash
    echo 5 | pyed 'line += "4"'  # 54 
    ```
* `n`: current line converted to an `int` if possible
    ```bash
    echo 5 | pyed 'n+2'  # 7 
    ```
* `text`: whole text, all lines together (only if `--whole` is set)
* `skip`: if set to `True`, current line will not be output

## Auto-import

* You can always import libraries you need manually.
* Some libraries are ready to be used: `re.* (match, search, findall), math.* (sqrt,...), datetime.* (datetime.now, ...)`
* Some others can auto-imported whenever its use has been detected. In such case, the line is reprocessed.
    * Functions: `Path, sleep, randint`
    * Modules: `pathlib, time, jsonpickle`

Caveat: When accessed first time, the auto-import makes the row reprocessed. It may influence you other in-script variables. Use verbose output to see if something has been auto-imported. 
```bash
echo -e "hey\nbuddy" | pyed 'a+=1; sleep(1); b+=1; line = a,b ' --setup "a=0;b=0;" -vv
Importing sleep from time
2, 1
3, 2
```



## Output
* Explicit assignment: By default, we output the `line`.
    ```bash
    echo "5" | pyed 'line = len(line)' # 1
    ```
* Single expression: If not set explicitly, we assign the expression to it automatically.
    ```bash
    echo "5" | pyed 'len(line)'  # 1 
    ```
* Tuple, generator: If `line` ends up as a tuple, its get joined by spaces.
    ```bash
    $ echo "5" | pyed 'line, len(line)'
    5, 1 
    ```
  
    Consider piping two lines 'hey' and 'buddy'. We return three elements, original text, reversed text and its length.
    ```bash
    $ echo -e "hey\nbuddy" | pyed 'line,line[::-1],len(line)' 
    hey, yeh, 3
    buddy, yddub, 5
    ```
* List: When `line` ends up as a list, its elements are printed to independent lines.
    ```bash
    $ echo "5" | pyed '[line, len(line)]'
    5
    1 
    ```

## CLI flags
* `command`: Any Python script (multiple statements allowed)
* `--setup`: Any Python script, executed before processing. Useful for variable initializing.
    Ex: prepend line numbers by incrementing a variable `count`.
    ```bash
    $ echo -e "row\nanother row" | pyed 'count+=1;line = f"{count}: {line}"'  --setup 'count=0'
    1: row
    2: another row
    ```
* `--verbose`: Show command exceptions. Used twice to show automatic imports. If you end up with no output, turn on to see what happened.
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
    $ echo -e "1\n2\n3\n4\n5" | pyed "int(line) > 3"  --filter
    4
    5
    ```
    The statement is equivalent to using `skip` (and not using `--filter`).
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pyed "skip = not int(line) > 3"
    4
    5
    ```
    When not using filter, `line` evaluates to `True` / `False`. By default, `False` or empty values are not output. 
    ```bash
    $ echo -e "1\n2\n3\n4\n5" | pyed "int(line) > 3"   
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
* `--empty` Output empty lines. (By default skipped.)  
    Consider shortening the text by 3 last letters. First line `hey` disappears completely then.
    ```bash
    $ echo -e "hey\nbuddy" | pyed 'line[:-3]'
    bu
    ```
    Should we insist on displaying, we see an empty line now.
    ```bash
    $ echo -e "hey\nbuddy" | pyed 'line[:-3]' --empty
    
    bu
    ```
