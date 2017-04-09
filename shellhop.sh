function _shellhop {
  READLINE_POINT=$(shellhop "$READLINE_LINE")
}

bind '"\C-xS0":beginning-of-line'
bind -x '"\C-xS1":"_shellhop"'
bind '"\C-x\C-f":"\C-xS0\C-xS1"'
