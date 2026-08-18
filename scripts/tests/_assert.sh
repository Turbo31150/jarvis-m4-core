#!/usr/bin/env bash
# Harness d'assertions minimal — sourcé par les tests.
: "${PASS:=0}"; : "${FAIL:=0}"
assert_eq(){
  local expected="${1:?assert_eq: arg1 (expected) missing}" actual="${2:?assert_eq: arg2 (actual) missing}" label="${3:?assert_eq: arg3 (label) missing}"
  if [ "$expected" = "$actual" ]; then PASS=$((PASS+1)); echo "  ✅ $label";
  else FAIL=$((FAIL+1)); echo "  ❌ $label — attendu='$expected' obtenu='$actual'"; fi
}
assert_contains(){ # $1=haystack $2=needle $3=label
  local haystack="${1:?assert_contains: arg1 (haystack) missing}" needle="${2:?assert_contains: arg2 (needle) missing}" label="${3:?assert_contains: arg3 (label) missing}"
  if printf '%s' "$haystack" | grep -qF "$needle"; then PASS=$((PASS+1)); echo "  ✅ $label";
  else FAIL=$((FAIL+1)); echo "  ❌ $label — '$needle' absent"; fi
}
assert_exit(){ # $1=code_attendu $2=code_obtenu $3=label
  local expected="${1:?assert_exit: arg1 (expected) missing}" actual="${2:?assert_exit: arg2 (actual) missing}" label="${3:?assert_exit: arg3 (label) missing}"
  assert_eq "$expected" "$actual" "$label (exit)"
}
report(){ echo "── $PASS pass / $FAIL fail ──"; [ "$FAIL" -eq 0 ]; }
