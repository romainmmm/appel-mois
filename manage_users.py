"""CLI to manage app accounts (run on the server).

Usage:
    python manage_users.py list
    python manage_users.py set <username> <role>     # role: gerant | reception
    python manage_users.py delete <username>

`set` prompts for the password (hidden). Data is stored in the SQLite database
(path from MOTEL_DB env var, or ./data/motel.db).
"""

import getpass
import os
import sys

import database
import auth

HERE = os.path.dirname(os.path.abspath(__file__))
ROLES = ("gerant", "reception")


def main(argv):
    conn = database.get_conn(database.db_path(HERE))
    users = database.load_users(conn)

    if not argv or argv[0] == "list":
        if not users:
            print("Aucun utilisateur. Créez-en un : python manage_users.py set <nom> <gerant|reception>")
        for name, rec in users.items():
            print(f"  {name}  [{rec.get('role','reception')}]")
        return

    cmd = argv[0]
    if cmd == "set" and len(argv) == 3:
        username, role = argv[1], argv[2]
        if role not in ROLES:
            print(f"Rôle invalide. Choisir parmi : {', '.join(ROLES)}")
            return
        pw = getpass.getpass(f"Mot de passe pour {username} : ")
        pw2 = getpass.getpass("Confirmer le mot de passe : ")
        if pw != pw2:
            print("Les mots de passe ne correspondent pas.")
            return
        if not pw:
            print("Le mot de passe ne peut pas être vide.")
            return
        users[username] = {"hash": auth.hash_password(pw), "role": role}
        database.save_users(conn, users)
        print(f"Utilisateur « {username} » ({role}) enregistré.")
    elif cmd == "delete" and len(argv) == 2:
        username = argv[1]
        if username in users:
            del users[username]
            database.save_users(conn, users)
            print(f"Utilisateur « {username} » supprimé.")
        else:
            print("Utilisateur introuvable.")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
