function _goto2 {
  READLINE_POINT=$(goto2 "$READLINE_LINE")
}

bind '"\key1":"\C-a"'
bind -x '"\key2":"_goto2"'
bind '"\C-k":"\key1\key2"'
