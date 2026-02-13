what command we should run to measure the coverage of your tests:
`python -m pytest --cov=src`

what total percent coverage you have achieved:
I have achieved 100% test coverage, it was surprisingly quick and easy with deep mode. Rather than going back and fourth as much I gave deep mode a solid prompt, went back and fourth a few times on strategy and expected behavior, and then it ran for around 45 minutes slowly adding tests that actually verify the expected behavior of the application and getting me to 100% coverage as well as near 100% branch coverage.

a list of exceptions that you could not cover. each of them should link to a block (a range of lines) of code in your repo, and then include the description mentioned above, explaining why this code is not covered. Again, you don't need to do more than 10 of these, and you can do zero of them if you have achieved 100% coverage of your editor.

The only part that doesn't have coverage is main.py because all it is is an event loop and system exit, not much to test.