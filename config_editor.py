import json
import tkinter as tk
from tkinter import messagebox
import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

class ConfigEditor:
    def __init__(self, master):
        self.master = master
        master.title("Config Editor")
        master.geometry("700x650")
        master.configure(bg="#f7f7f7")
        default_font = ("Segoe UI", 10)
        bold_font = ("Segoe UI", 10, "bold")

        self.load_config()

        self.vars = {
            "notify_on_start": tk.BooleanVar(value=self.config["telegram"].get("notify_on_start", True)),
            "notify_on_end": tk.BooleanVar(value=self.config["telegram"].get("notify_on_end", True)),
            "notify_summary_start": tk.BooleanVar(value=self.config["telegram"].get("notify_summary_start", True)),
            "notify_summary_end": tk.BooleanVar(value=self.config["telegram"].get("notify_summary_end", True)),
            "notify_errors": tk.BooleanVar(value=self.config["telegram"].get("notify_errors", True)),
            "send_xml_file": tk.BooleanVar(value=self.config["telegram"].get("send_xml_file", True)),
            "email_notify": tk.BooleanVar(value=self.config["email"].get("notify", True))
        }

        row = 0
        tk.Label(master, text="Telegram Optionen", font=bold_font, bg="#e0e0e0", anchor="w").grid(row=row, column=0, columnspan=2, sticky="we", pady=(10, 0), padx=10)
        row += 1

        for label, varname in [
            ("Stream gestartet", "notify_on_start"),
            ("Stream beendet", "notify_on_end"),
            ("Übersicht bei Start", "notify_summary_start"),
            ("Übersicht bei Ende", "notify_summary_end"),
            ("Fehlermeldungen senden", "notify_errors"),
            ("Monats-XML senden", "send_xml_file")
        ]:
            cb = tk.Checkbutton(master, text=label, variable=self.vars[varname], font=default_font, bg="#f7f7f7")
            cb.grid(row=row, column=0, columnspan=2, sticky="w", padx=20)
            row += 1

        tk.Label(master, text="E-Mail Optionen", font=bold_font, bg="#e0e0e0", anchor="w").grid(row=row, column=0, columnspan=2, sticky="we", pady=(10, 0), padx=10)
        row += 1

        cb = tk.Checkbutton(master, text="E-Mail Benachrichtigung aktiv", variable=self.vars["email_notify"], font=default_font, bg="#f7f7f7")
        cb.grid(row=row, column=0, columnspan=2, sticky="w", padx=20)
        row += 1

        self.secret_paths = {
            "telegram": self.config["telegram"]["credentials_file"],
            "telegram_anzeige": self.config["telegram"].get("credentials_file_anzeige", "secrets/telegram_anzeige.json"),
            "email": self.config["email"]["credentials_file"],
            "obs": self.config["obs"]["password_file"]
        }
        self.secrets = {
            key: self.load_json_secret(path) for key, path in self.secret_paths.items()
        }
        self.entries = {}

        for title, section_key, fields in [
            ("Telegram Bot 1 (St_Gisela)", "telegram", ["token", "chat_id"]),
            ("Telegram Bot 2 (Anzeige)", "telegram_anzeige", ["token", "chat_id"]),
            ("E-Mail Zugangsdaten", "email", ["email", "app_password"]),
            ("OBS Zugangsdaten", "obs", ["password"])
        ]:
            tk.Label(master, text=title, font=bold_font, bg="#e0e0e0", anchor="w").grid(row=row, column=0, columnspan=2, sticky="we", pady=(10, 0), padx=10)
            row += 1
            for field in fields:
                lbl = tk.Label(master, text=field, font=default_font, bg="#f7f7f7")
                lbl.grid(row=row, column=0, sticky="e", padx=(10, 5), pady=2)
                entry = tk.Entry(master, width=60, font=default_font)
                entry.insert(0, self.secrets.get(section_key, {}).get(field, ""))
                entry.grid(row=row, column=1, sticky="w", padx=(0, 10), pady=2)
                self.entries[f"{section_key}_{field}"] = entry
                row += 1

        tk.Button(master, text="Speichern", command=self.save_all, bg="#4CAF50", fg="white", font=default_font, padx=10, pady=5, width=15).grid(row=row, column=0, pady=20, padx=10)
        tk.Button(master, text="Abbrechen", command=master.quit, bg="#f44336", fg="white", font=default_font, padx=10, pady=5, width=15).grid(row=row, column=1, pady=20, sticky="e", padx=10)

    def load_config(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def load_json_secret(self, path):
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_all(self):
        self.config["telegram"]["notify_on_start"] = self.vars["notify_on_start"].get()
        self.config["telegram"]["notify_on_end"] = self.vars["notify_on_end"].get()
        self.config["telegram"]["notify_summary_start"] = self.vars["notify_summary_start"].get()
        self.config["telegram"]["notify_summary_end"] = self.vars["notify_summary_end"].get()
        self.config["telegram"]["notify_errors"] = self.vars["notify_errors"].get()
        self.config["telegram"]["send_xml_file"] = self.vars["send_xml_file"].get()
        self.config["email"]["notify"] = self.vars["email_notify"].get()

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, sort_keys=False, allow_unicode=True)

        updated = {
            "telegram": {
                "token": self.entries["telegram_token"].get(),
                "chat_id": self.entries["telegram_chat_id"].get()
            },
            "telegram_anzeige": {
                "token": self.entries["telegram_anzeige_token"].get(),
                "chat_id": self.entries["telegram_anzeige_chat_id"].get()
            },
            "email": {
                "email": self.entries["email_email"].get(),
                "app_password": self.entries["email_app_password"].get()
            },
            "obs": {
                "password": self.entries["obs_password"].get()
            }
        }

        for section, data in updated.items():
            path = os.path.join(os.path.dirname(__file__), self.secret_paths[section])
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        messagebox.showinfo("Gespeichert", "Konfiguration und Zugangsdaten wurden aktualisiert.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()
