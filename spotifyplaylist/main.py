# moteur
# permet de dl le mp3 et de l'ajouter au dossier de la playlist
import yt_dlp # pour dl le mp3 et cover
import os
import shutil
from mutagen.mp3 import MP3 # pour les infos 
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, error # pour les infos

def mettre_a_jour_tags_mp3(fichier_mp3, titre, artiste, album, image_path=None):
    """
    ajoute ou met à jour les tags ID3 (texte et image) du mp3
    """
    try:
        audio = MP3(fichier_mp3, ID3=ID3)
    except error:
        # si il en a pas on en crée
        audio = MP3(fichier_mp3)
        audio.tags = ID3()
    
    # supp les old tags pour pas de bug
    audio.tags.delall('TIT2')
    audio.tags.delall('TPE1')
    audio.tags.delall('TALB')
    audio.tags.delall('APIC')

    
    audio.tags.add(TIT2(encoding=3, text=titre))      # TIT2 = titre
    audio.tags.add(TPE1(encoding=3, text=artiste))  # TPE1 = artiste
    audio.tags.add(TALB(encoding=3, text=album))    # TALB = album

    # add de la cover
    if image_path:
        try:
            # savoir le type de fichier
            if image_path.lower().endswith('.png'):
                mime_type = 'image/png'
            else:
                # le reste est considerer comme du jpeg
                mime_type = 'image/jpeg'
                
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
            
            audio.tags.add(
                APIC(
                    encoding=3,         # 3 = utf-8
                    mime=mime_type,
                    type=3,             # 3 = front cover
                    desc='Cover',
                    data=image_data
                )
            )
            print(f"Cover '{os.path.basename(image_path)}' ajoutée avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'image : {e}")
    else:
        print("Aucune image de couverture trouvée.")
    
    # save des tags
    audio.save(v2_version=3)


class SpotifyLocalEngine:
    def __init__(self, spotify_local_path: str):
        self.spotify_local_path = spotify_local_path
        if not os.path.exists(self.spotify_local_path):
            os.makedirs(self.spotify_local_path)
            
        
        
        self.temp_dir = os.path.join(os.path.dirname(__file__) or '.', "dltemp")
        os.makedirs(self.temp_dir, exist_ok=True)


    def download_and_add(self, url: str) -> str:
        try:
            # si cest un fichier local
            if os.path.isfile(url):
                nom_fichier = os.path.basename(url)
                temp_path = os.path.join(self.temp_dir, nom_fichier)
                shutil.copy2(url, temp_path)
                
                dest = os.path.join(self.spotify_local_path, nom_fichier)
                if os.path.exists(dest):
                    os.remove(temp_path) # Nettoyer le temp
                    return f"Le fichier {nom_fichier} existe déjà dans le dossier local Spotify"
                
                shutil.move(temp_path, dest)
                return f"Fichier local ajouté : {nom_fichier}"

            # option de yt-dlp
            options = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'writethumbnail': True,  # dl la cover
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            print(f"⬇Téléchargement de '{url}'...")
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'musique_inconnue')
                artist = info.get('artist') or info.get('uploader') or 'inconnu'
                album = info.get('album', '')

            # traitement apres dl
            
            # trouver les fichier dans dltemp
            files_in_temp = os.listdir(self.temp_dir)
            mp3_path = None
            image_path = None

            for f in files_in_temp:
                if f.endswith('.mp3'):
                    mp3_path = os.path.join(self.temp_dir, f)
                
                elif f.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    image_path = os.path.join(self.temp_dir, f)

            # check le mp3
            if not mp3_path:
                # clear l'old cover si y'en a une
                if image_path: os.remove(image_path)
                return f"Erreur : Aucun fichier MP3 n'a été créé."

            # check si ya deja le ficiher
            nom_fichier_mp3 = os.path.basename(mp3_path)
            dest_path = os.path.join(self.spotify_local_path, nom_fichier_mp3)
            
            if os.path.exists(dest_path):
                # clear des fichier temps
                os.remove(mp3_path)
                if image_path: os.remove(image_path)
                return f"Le fichier {nom_fichier_mp3} existe déjà."

            # add les tags
            print(f"Ajout des tags à '{nom_fichier_mp3}'...")
            mettre_a_jour_tags_mp3(mp3_path, title, artist, album, image_path)

            # move le mp3 avec les tags
            shutil.move(mp3_path, dest_path)
            
            # clear la cover tempo
            if image_path:
                os.remove(image_path)

            return f"{title} ajouté avec succès (avec cover) !"

        except Exception as e:
            # clear le tout au cas ou
            print(f"Erreur lors du téléchargement ou ajout : {str(e)}")
            print("Nettoyage du dossier temporaire...")
            for f in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, f))
            return f"Erreur : {str(e)}"

if __name__ == "__main__":
    print("=== Spotify Local Engine ===")
    lien = input("Lien de la musique : ").strip()
    dossier = input("Chemin du dossier de la playlist Spotify : ").strip()

    moteur = SpotifyLocalEngine(dossier)
    resultat = moteur.download_and_add(lien)
    print(resultat)