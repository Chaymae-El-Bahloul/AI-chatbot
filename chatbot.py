"""AI ChatBot en ligne de commande (historique sauvegarde dans SQLite)."""

import sys

import db
from core import file_to_part, get_client, stream_reply

HELP = """Commandes disponibles :
  /help          afficher cette aide
  /new           demarrer une nouvelle conversation
  /history       lister les conversations sauvegardees
  /open ID       reprendre une conversation
  /reset         effacer les messages de la conversation courante
  /lang X        forcer la langue (ex: /lang espagnol), /lang auto pour revenir a l'auto
  /file CHEMIN   joindre une image, un PDF ou un fichier texte au prochain message
  /quit          quitter
"""


def main() -> None:
    try:
        client = get_client()
    except RuntimeError as exc:
        sys.exit(f"Erreur : {exc}")

    db.init_db()
    state = {"conv": db.create_conversation(), "lang": None, "files": []}
    print("AI ChatBot (tape /help pour l'aide)")

    while True:
        try:
            text = input("\nToi > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break
        if not text:
            continue

        if text.startswith("/"):
            name, _, arg = text.partition(" ")
            arg = arg.strip()
            if name == "/quit":
                print("Au revoir.")
                break
            elif name == "/help":
                print(HELP)
            elif name == "/new":
                state["conv"] = db.create_conversation()
                print("Nouvelle conversation.")
            elif name == "/history":
                for c in db.list_conversations():
                    print(f"  [{c['id']}] {c['title']}  ({c['created_at']})")
            elif name == "/open" and arg.isdigit():
                state["conv"] = int(arg)
                for m in db.get_messages(state["conv"]):
                    who = "Toi" if m["role"] == "user" else "Bot"
                    print(f"{who} > {m['content']}")
            elif name == "/reset":
                db.clear_messages(state["conv"])
                print("Messages effaces.")
            elif name == "/lang":
                state["lang"] = None if arg in ("", "auto") else arg
                print(f"Langue : {state['lang'] or 'detection automatique'}")
            elif name == "/file":
                try:
                    with open(arg, "rb") as f:
                        state["files"].append(file_to_part(arg, f.read()))
                    print(f"Fichier ajoute : {arg}")
                except (OSError, ValueError) as exc:
                    print(f"[Erreur] {exc}")
            else:
                print("Commande inconnue. Tape /help.")
            continue

        history = db.get_messages(state["conv"])
        reply = []
        try:
            print("Bot > ", end="", flush=True)
            for piece in stream_reply(client, history, text, state["files"], state["lang"]):
                reply.append(piece)
                print(piece, end="", flush=True)
            print()
        except Exception as exc:
            print(f"\n[Erreur API] {exc}")
            continue

        db.add_message(state["conv"], "user", text)
        db.add_message(state["conv"], "assistant", "".join(reply))
        if not history:
            db.rename_conversation(state["conv"], text[:40])
        state["files"] = []


if __name__ == "__main__":
    main()