function _goto2 {
  READLINE_POINT=$(goto2 "$READLINE_LINE")
}

bind -x '"\C-k":"_goto2"'
