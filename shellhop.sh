function _shellhop {
  READLINE_POINT=$(shellhop "$READLINE_LINE")
}

bind '"\key1":"\C-a"'
bind -x '"\key2":"_shellhop"'
bind '"\C-k":"\key1\key2"'
