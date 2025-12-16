import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
from tkextrafont import Font

import json
import os
import sys

# pour le ffmpeg
import requests
import zipfile
import io

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

CONFIG_FILE = get_app_path("config.json")

def resource_path(relative_path):
    """retourne le chemin absolu vers le fichier ressource"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def dl_ffmpeg():
    """check et dl ffmpeg si besoin"""
    ffmpeg_path = get_app_path("ffmpeg.exe")
    ffprobe_path = get_app_path("ffprobe.exe")

    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        print("FFmpeg deja la")
        return True
    
    print("Telechargement de FFmpeg ...")

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # dire l'erreur si ya un probleme

        z = zipfile.ZipFile(io.BytesIO(response.content))

        ffmpeg_file_path = None
        ffprobe_file_path = None

        for file in z.namelist():
            if file.endswith("/bin/ffmpeg.exe"):
                ffmpeg_file_path = file
            if file.endswith("/bin/ffprobe.exe"):
                ffprobe_file_path = file

        if not ffmpeg_file_path or not ffprobe_file_path:
            messagebox.showerror("Erreur FFmpeg", "Impossible de trouver les fichiers dans le zip.")
            return False
        
        app_dir = get_app_path(".")# le dossier ou est l'exe

        #extraire les .exe
        ffmpeg_data = z.read(ffmpeg_file_path)
        with open(ffmpeg_path, 'wb') as f:
            f.write(ffmpeg_data)

        ffprobe_data = z.read(ffprobe_file_path)
        with open(ffprobe_path, 'wb') as f:
            f.write(ffprobe_data)

        z.close
        print("FFmpeg dl et extrait avec succes")
        return True
    
    except Exception as e:
        messagebox.showerror("Erreur de téléchargement", f"impossible de télécharger FFmpeg : {e}")
        return False


def save_config(spotify_path):
    """ save le local path et le flag setup_done"""
    config = {"spotify_local_path": spotify_path} # noter le path du dossier playlist 
    print("Tentative d'ecriture du fichier confing.json...")
    with open(CONFIG_FILE, 'w')as f:
        json.dump(config, f, indent=4) # indent = indentation

def choose_folder():
    path = filedialog.askdirectory(title="Choisir le dossier pour la playlist local")
    if path:
        spotify_path_var.set(path)

def finish_setup():
    """verifier le dossier et terminer le setup"""
    path = spotify_path_var.get()
    if not path or not os.path.exists(path):
        messagebox.showerror("Erreur", "Veuiller chosir un fichier valide.")
        return
    
    try:
        button_finish.config(text="Téléchargement de FFmpeg...", state="disabled")
        root.update_idletasks()# force la maj du texte

        if not dl_ffmpeg():
            button_finish.config(text="J'ai terminé", state="normal")
            return
        
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur inattendue : {e}")
        button_finish.config(text="J'ai terminé", state="normal")
        return
    
    save_config(path)
    messagebox.showinfo("Setup fini", "Vous pouvez maintenant utiliser le logiciel.")
    root.destroy()# fermer la fenetre setup


# Création de la fenetre

root = ttk.Window(title="Configuration Spotify Local", themename="darkly") # creation de la fenetre
root.geometry("600x400") # taille de la fenetre
root.resizable(False, False) # impossible de resize la fenetre

# chargement de la font
FONT_PATH = "assets/circular-std-medium-500.ttf"
FONT_NAME = "Circular Std Medium"


try:
    bundled_font_path = resource_path(FONT_PATH)
    Font(file=bundled_font_path, family=FONT_NAME) 
    
    font_circular_title = tkfont.Font(family=FONT_NAME, size=16, weight="bold")
    font_circular_text = tkfont.Font(family=FONT_NAME, size=10)
    font_circular_button = tkfont.Font(family=FONT_NAME, size=10, weight="bold")

    style = ttk.Style()
    style.configure("TButton", font=font_circular_button)

except Exception as e:
    print(f"Erreur lors du chargement de la police: {e}. Fallback sur Arial")
    font_circular_title = tkfont.Font(family="Arial", size=16, weight="bold")
    font_circular_text = tkfont.Font(family="Arial", size=10)
    font_circular_button = tkfont.Font(family="Arial", size=10, weight="bold")

    style = ttk.Style()
    style.configure("TButton", font=font_circular_button)


ttk.Label(root, text="Bienvenue !", font=font_circular_title, bootstyle="success").pack(pady=10)# bold = gras //  pack pady = espacement vertical
ttk.Label(root, text="Avant d'utiliser le logiciel, vous devez activer les fichiers locaux dans Spotify.", font=font_circular_text, wraplength=450).pack(pady=10) # wraplenght = longeur de la ligne

# instruction pour faire le fichier pour spotify
instructions = (
    "1. Ouvrir Spotify sur pc\n"
    "2. Clicker sur les 3 points en haut a gauche, puis dans 'Modifier' et 'Préférences' (ou Ctrl + P)\n"
    "3. Descendre jusqu'à 'Bibliothèque' et activer 'Afficher les fichiers locaux'\n"
    "4. Cliquer sur 'Ajouter une source' et chosir le fichier ou sera stocké la playlist local.\n"
    )
ttk.Label(root, text=instructions, font=font_circular_text, wraplength=450).pack(pady=10)

# choix du dossier
spotify_path_var = ttk.StringVar()
ttk.Entry(root, textvariable=spotify_path_var, width=50, font=font_circular_text).pack(pady=5)# permet de mettre le chemin du dossier dans l'entry
ttk.Button(root, text="Choisir dossier (le meme que pour Spotify)", command=choose_folder, style="TButton").pack(pady=5)

button_finish = ttk.Button(root, text="J'ai terminé", command=finish_setup, style="TButton")
button_finish.pack(pady=15)

ICON_PATH_FILE = "assets/logo.ico"

try:
    icon_path = resource_path(ICON_PATH_FILE)
    photo = tk.PhotoImage(file=icon_path)
    root.iconbitmap(False, photo)
except Exception as e:
    print(f"Bug a cause de : {e}")

root.mainloop()