#!/usr/bin/env bash
# bash completion for pz
_pz()
{
  local cur
  local cmd

  cur=${COMP_WORDS[$COMP_CWORD]}
  cmd=( ${COMP_WORDS[@]} )

  if [[ "$cur" == -* ]]; then
    COMPREPLY=( $( compgen -W "-h --help -v --verbose -q --quiet -S --setup -E --end -F --filter -f --format -w --whole -n -1 -0 --empty -g --generate --stderr --overflow-safe --search --match --findall --sub" -- $cur ) )
    return 0
  fi
}

complete -F _pz -o default pz
