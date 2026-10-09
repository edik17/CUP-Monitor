"""Helper script per esportare i Secrets necessari a GitHub Actions (Strada 1)."""
from pathlib import Path
import sys

# Forza stdout in UTF-8 su Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    root = Path(__file__).parent.resolve()
    config_file = root / "config.yaml"
    session_file = root / "session" / "state.json"
    secrets_dir = root / "github_secrets"
    secrets_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("CONFIGURAZIONE GITHUB SECRETS PER GITHUB ACTIONS (STRADA 1)")
    print("=" * 70)
    print("Link diretto per aggiungere i Secrets sul tuo repository:")
    print("-> https://github.com/edik17/CUP-Monitor/settings/secrets/actions/new\n")

    if not config_file.exists():
        print("ERRORE: File config.yaml non trovato!")
        return 1

    config_content = config_file.read_text(encoding="utf-8").strip()
    (secrets_dir / "CUP_CONFIG_YAML.txt").write_text(config_content, encoding="utf-8")
    print("1) SECRET NOME: CUP_CONFIG_YAML")
    print("   Salvato pronto da copiare in: github_secrets/CUP_CONFIG_YAML.txt")
    print("-" * 50)

    if session_file.exists() and session_file.stat().st_size > 0:
        session_content = session_file.read_text(encoding="utf-8").strip()
        (secrets_dir / "CUP_SESSION_STATE.txt").write_text(session_content, encoding="utf-8")
        print("2) SECRET NOME: CUP_SESSION_STATE")
        print("   Salvato pronto da copiare in: github_secrets/CUP_SESSION_STATE.txt")
        print("-" * 50)
    else:
        print("ATTENZIONE: File session/state.json non trovato o vuoto.")

    print("\nI file di testo sono pronti nella cartella 'github_secrets'!")
    print("Puoi aprirli con Blocco Note e incollarli su GitHub in 1 minuto.")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
