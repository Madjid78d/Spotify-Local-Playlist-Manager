# use ttkbootstrap a la place de tkinter pour le style de l'app
import ttkbootstrap as ttk
from ttkbootstrap.constants import * # pour les styles
from ttkbootstrap.widgets.scrolled import ScrolledText # fonction scroll de ttk
from tkinter import filedialog, messagebox # eux sont aps dans ttk donc on keep
import tkinter as tk
import tkinter.font as tkfont
from tkextrafont import Font

# autre import
import os
import json
from main import SpotifyLocalEngine # le moteur
import sys # pour les fichiers

def get_app_path(relative_path):
    """
    retourne le chemin absolu vers le fichier
    """
    if getattr(sys, 'frozen', False):
        # si exe
        base_path = os.path.dirname(sys.executable)
    else:
        # si py
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)
    

CONFIG_FILE_NAME = get_app_path("config.json")


def resource_path(relative_path):
    """Retourne le chemin absolu vers le fichier de ressources."""
    try:
        # chemin dans le bundle pyinstaller
        base_path = sys._MEIPASS
    except Exception:
        # chemin en mode dev
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class SpotifyManagerApp:
    def __init__(self, master):
        self.master = master

        FONT_PATH = "assets/circular-std-medium-500.ttf"
        FONT_NAME = "Circular Std Medium"
        try:
            # chemin de la police dans le bundle
            bundled_font_path =  resource_path(FONT_PATH)

            Font(file=bundled_font_path, family=FONT_NAME)

            self.font_circular_text = tkfont.Font(family=FONT_NAME, size=16, weight="bold")
            self.font_circular_label = tkfont.Font(family=FONT_NAME, size=12)
            self.font_circular_button = tkfont.Font(family=FONT_NAME, size=10, weight="bold")
            self.font_circular_log = tkfont.Font(family=FONT_NAME, size=10)

            style = ttk.Style()
            style.configure("TButton", font=self.font_circular_button)
            style.configure("TLabel", font=self.font_circular_label)


        except Exception as e:
            print(f"Erreur chargement police : {e}. Fallback sur Arial.")
            self.font_circular_text = tkfont.Font(family="Arial", size=16, weight="bold")
            self.font_circular_label = tkfont.Font(family="Arial", size=12)  
            self.font_circular_button = tkfont.Font(family="Arial", size=10, weight="bold")
            self.font_circular_log = tkfont.Font(family="Arial", size=10)   

            style = ttk.Style()
            style.configure("TButton", font=self.font_circular_button)
            style.configure("TLabel", font=self.font_circular_label)

        self.spotify_folder = self._load_config()
        self.moteur = SpotifyLocalEngine(self.spotify_folder)

        self.entry_var = tk.StringVar()
        
        self._create_widgets()

        self.log(f"Moteur initialisé. Chemin cible : {self.spotify_folder}")

    def _load_config(self):
        """verifie et charge le chemin spotify depuis le fichier de configuration"""

        CONFIG_FILE = get_app_path(CONFIG_FILE_NAME)
        # check si ya la config
        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("Erreur de configuration", "Setup non trouvé. Lancez setup.py avant.")
            self.master.quit() # Quitte l'application Tkinter
            return None

        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            
            spotify_folder = config.get("spotify_local_path")

            if not spotify_folder or not os.path.exists(spotify_folder):
                messagebox.showerror("Erreur de configuration", f"Le chemin Spotify Local ({spotify_folder}) est invalide. Vérifiez {CONFIG_FILE}.")
                self.master.quit()
                return None
            
            return spotify_folder

        except json.JSONDecodeError:
            messagebox.showerror("Erreur de configuration", f"Le fichier {CONFIG_FILE} est mal formé (JSON invalide).")
            self.master.quit()
            return None
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de chargement de configuration : {e}")
            self.master.quit()
            return None


    def log(self, msg):
        """Aadd un message dans les logs"""
        self.log_box.text['state'] = 'normal' 
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.text['state'] = 'disabled'

    def choose_file(self):
        """chosir un fichier local"""
        path = filedialog.askopenfilename(
            title="Choisir un fichier audio",
            filetypes=[("Audio files", "*.mp3 *.wav *.flac")]
        )
        if path:
            self.entry_var.set(path)

    def add_song(self):
        """lance le dl"""
        url_or_file = self.entry_var.get().strip()
        
        if not url_or_file:
            messagebox.showwarning("Attention", "Entrez un lien ou choisissez un fichier.")
            return

        self.log(f"\nTâche lancée : {url_or_file}")
        
        # desac l'entree pendant le traitement pour pas double clic
        self.add_button.configure(state="disabled", text="Traitement...") # use configure de ttk a la place de config de tk
        self.entry_field.configure(state="disabled")

        # execut moteur
        resultat = self.moteur.download_and_add(url_or_file)
        
        self.log(resultat)
        
        # reac interface
        self.add_button.configure(state="normal", text="Télécharger et ajouter")
        self.entry_field.configure(state="normal")
        self.entry_var.set("") # clear apres

    def _create_widgets(self):
        """elements graphique de la fenetre"""
        # champ de saise
        ttk.Label(self.master, text="Lien ou fichier audio :").pack(pady=5)
        self.entry_field = ttk.Entry(self.master, textvariable=self.entry_var, width=60)
        self.entry_field.pack(pady=5)

        # boutton
        ttk.Button(self.master, text="Choisir un fichier local", command=self.choose_file, bootstyle="secondary-outline", style="TButton").pack(pady=5) # bootstyle = info-outline pour ressembler au boutton de tk
        self.add_button = ttk.Button(self.master, text="Télécharger et ajouter", command=self.add_song, bootstyle="success", style="TButton") # succes = vert
        self.add_button.pack(pady=5)

        # les logs
        ttk.Label(self.master, text="Logs du Moteur :").pack()
        self.log_box = ScrolledText(self.master, width=60, height=10, state="disabled", autohide=True) # autohide = True pour ne pas afficher la scrollbar si pas besoin
        self.log_box.pack(pady=5)

        self.log_box.text.config(font=self.font_circular_log)


if __name__ == "__main__":
    root = ttk.Window(title="Spotify Local Playlist Manager", themename="darkly")# themename="cosmo" = theme de ttkbootstrap
    root.geometry("600x400")
    root.resizable(False, False)

    ICON_PATH_FILE = "assets/logo.ico"

    try:
        icon_path = resource_path(ICON_PATH_FILE)
        photo = tk.PhotoImage(file=icon_path)
        root.iconbitmap(False, photo)
    except Exception as e:
        print(f"Bug a cause de : {e}")

    app = SpotifyManagerApp(root)
    if app.spotify_folder:
        root.mainloop()