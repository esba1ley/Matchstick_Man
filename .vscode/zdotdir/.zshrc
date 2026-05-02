# Project-local zsh init for VS Code integrated terminals.
#
# VS Code launches the integrated terminal with ZDOTDIR pointing at this
# directory (see ../settings.json -> terminal.integrated.profiles.osx).
# zsh therefore sources THIS file instead of ~/.zshrc.
#
# We layer the user's normal interactive setup on top, then activate the
# project's conda env. Because the project env activation runs *after* the
# user's .zshrc, it overrides any default-env activation done there.

# 1. Source the user's normal interactive zsh setup (Oh My Zsh, aliases, etc.).
#    Temporarily restore ZDOTDIR so anything in ~/.zshrc that references it
#    behaves normally.
if [[ -f "$HOME/.zshrc" ]]; then
    ZDOTDIR="$HOME" source "$HOME/.zshrc"
fi

# 2. Deactivate any conda env(s) ~/.zshrc may have activated, so we start
#    matchstick from a clean state. The loop handles stacked envs; the bounded
#    iteration count guards against `conda deactivate` ever failing to unset
#    CONDA_DEFAULT_ENV.
for _ in 1 2 3 4 5; do
    [[ -z "${CONDA_DEFAULT_ENV:-}" ]] && break
    conda deactivate 2>/dev/null || break
done

# 3. Activate the project conda env. Prefer mamba; fall back to conda.
#    Silent on failure so a missing env doesn't prevent the terminal opening.
if command -v mamba >/dev/null 2>&1; then
    mamba activate matchstick 2>/dev/null || true
elif command -v conda >/dev/null 2>&1; then
    conda activate matchstick 2>/dev/null || true
fi
