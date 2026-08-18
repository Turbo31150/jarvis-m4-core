# =============================================================================
# ENVIRONNEMENT EXACT RÉMI LINUX (SSH REBOND & M6 CLUSTER)
# =============================================================================
export USER=remi
export LOGNAME=remi
export HOME=/home/pamerys

# Prompt PS1 coloré style Rémi Linux
export PS1='\[[01;35m\]remi@remi-linux\[[00m\]:\[[01;36m\]\w\[[00m\]$ '

export OLLAMA_HOST="http://100.113.121.61:11434"
export LM_HOST="http://10.42.0.230:1234"
export M6_HOST="http://10.42.0.230:1234"
export PATH="/home/pamerys/.local/bin:/usr/local/bin:/usr/bin:/bin:/home/pamerys/.gemini/antigravity-cli/bin:/home/pamerys/.local/bin:/home/pamerys/.bun/bin:/home/turbo/.local/bin:/home/pamerys/bin:/home/turbo/.opencode/bin:/home/pamerys/.local/bin:/home/pamerys/.bun/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin/home/turbo/.lmstudio/bin:/snap/bin"

alias ls='ls --color=auto'
alias ll='ls -alF'
alias la='ls -A'
alias ssh-m6="ssh turbo@10.42.0.230"
alias ssh-remi="ssh turbo@100.113.121.61"
alias ollama-remote="OLLAMA_HOST=http://100.113.121.61:11434 ollama"
alias lm-m6="curl -s http://10.42.0.230:1234/v1/models | jq ."

echo "=================================================="
echo "  💻 SESSION RÉMI LINUX — CLUSTER & GPU DÉPORTÉS"
echo "=================================================="
echo "🔗 Connecté: Ollama Rémi (100.113.121.61:11434) | LM Studio Dual GPU M6 (10.42.0.230:1234)"
