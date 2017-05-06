# shellhop

[![Build Status](https://travis-ci.org/rlane/shellhop.svg?branch=master)](https://travis-ci.org/rlane/shellhop)
[![Coverage Status](https://coveralls.io/repos/github/rlane/shellhop/badge.svg?branch=master)](https://coveralls.io/github/rlane/shellhop?branch=master)

Shellhop adds incremental search of your command line to bash and zsh. It's
similar to <kbd>Ctrl-S</kbd> and <kbd>Ctrl-R</kbd>, but it searches only within
the current line and highlights all matches.

![shellhop demo](http://i.imgur.com/9o8S8Uu.gif)

## Installation

Build shellhop:

    git clone git://github.com/rlane/shellhop
    cd shellhop
    make

Add this to your bashrc:

    eval $(/path/to/shellhop --bash)

You can change the keybinding (default <kbd>Ctrl-X Ctrl-F</kbd>) with the
`--key` option:

    eval $(/path/to/shellhop --bash --key \\C-S)

Zsh is also supported:

    eval $(/path/to/shellhop --zsh)

## Usage

When editing a command line, type <kbd>Ctrl-X Ctrl-F</kbd>. You'll see a
`(shellhop)` prompt followed by the line. Start typing the text at the location
you wish to move the cursor to. Matches will be highlighted as you type. When
there is a unique match, hit <kbd>Enter</kbd> to accept it. Shellhop will exit
and leave the cursor in the desired position.

Use <kbd>Ctrl-N</kbd> and <kbd>Ctrl-P</kbd> to cycle between multiple matches.
The current match will be highlighted and the others underlined.

## Contributing

Fork the project and send a pull request.

To run the test suite:

    python test.py

Be sure to add a new test if contributing a feature or bugfix.

## Related

- [goto](https://github.com/Fakerr/goto)
- [zsh-vi-search](https://github.com/soheilpro/zsh-vi-search)

## License

Copyright 2017 Rich Lane

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
