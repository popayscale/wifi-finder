import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import xml.etree.ElementTree as ET
import tempfile

class WifiKeyViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualiseur de Clés WiFi")
        self.root.geometry("600x400")
        
        # Dictionnaire pour stocker les informations des réseaux
        self.wifi_info = {}
        
        # Frame principale
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame gauche pour la liste
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Label pour la liste
        ttk.Label(left_frame, text="Réseaux WiFi enregistrés:").grid(row=0, column=0, pady=5)

        # Listbox pour les réseaux
        self.wifi_listbox = tk.Listbox(left_frame, width=30, height=15)
        self.wifi_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar pour la listbox
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.wifi_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.wifi_listbox.configure(yscrollcommand=scrollbar.set)

        # Frame droite pour les détails
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame pour les informations du réseau
        info_frame = ttk.LabelFrame(right_frame, text="Informations du réseau", padding="5")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Labels pour les informations
        self.ssid_label = ttk.Label(info_frame, text="SSID: ")
        self.ssid_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.auth_label = ttk.Label(info_frame, text="Authentification: ")
        self.auth_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.encryption_label = ttk.Label(info_frame, text="Chiffrement: ")
        self.encryption_label.grid(row=2, column=0, sticky=tk.W, pady=2)

        # Frame pour la clé
        key_frame = ttk.LabelFrame(right_frame, text="Clé du réseau", padding="5")
        key_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # Zone de texte pour la clé
        self.key_text = tk.Text(key_frame, width=30, height=2)
        self.key_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Boutons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(button_frame, text="Copier la clé", command=self.copy_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Rafraîchir", command=self.refresh_networks).pack(side=tk.LEFT, padx=5)

        # Configuration du redimensionnement
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Binding pour la sélection dans la liste
        self.wifi_listbox.bind('<<ListboxSelect>>', self.show_network_info)

        # Création d'un répertoire temporaire pour les exports
        self.temp_dir = tempfile.mkdtemp()

        # Chargement initial des réseaux
        self.refresh_networks()

    def get_wifi_profiles(self):
        try:
            # Export de tous les profils WiFi
            export_command = f'netsh wlan export profile folder="{self.temp_dir}" key=clear'
            subprocess.run(export_command, shell=True, capture_output=True)
            
            profiles = {}
            # Lecture de tous les fichiers XML exportés
            for filename in os.listdir(self.temp_dir):
                if filename.endswith(".xml"):
                    file_path = os.path.join(self.temp_dir, filename)
                    try:
                        tree = ET.parse(file_path)
                        root = tree.getroot()
                        
                        # Namespace pour les éléments XML
                        ns = {'ns': 'http://www.microsoft.com/networking/WLAN/profile/v1'}
                        
                        # Extraction des informations
                        ssid = root.find('.//ns:SSID/ns:name', ns).text
                        auth = root.find('.//ns:authentication', ns).text
                        encryption = root.find('.//ns:encryption', ns).text
                        
                        # Recherche de la clé (peut être absente)
                        key_element = root.find('.//ns:keyMaterial', ns)
                        key = key_element.text if key_element is not None else "Pas de clé"
                        
                        profiles[ssid] = {
                            'auth': auth,
                            'encryption': encryption,
                            'key': key
                        }
                        
                        # Suppression du fichier après lecture
                        os.remove(file_path)
                        
                    except Exception as e:
                        print(f"Erreur lors de la lecture du fichier {filename}: {str(e)}")
                        continue
            
            return profiles
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de récupérer les profils WiFi: {str(e)}")
            return {}

    def refresh_networks(self):
        self.wifi_listbox.delete(0, tk.END)
        self.wifi_info = self.get_wifi_profiles()
        
        # Tri des réseaux par ordre alphabétique
        for ssid in sorted(self.wifi_info.keys()):
            self.wifi_listbox.insert(tk.END, ssid)

    def show_network_info(self, event):
        selection = self.wifi_listbox.curselection()
        if selection:
            ssid = self.wifi_listbox.get(selection[0])
            info = self.wifi_info.get(ssid, {})
            
            # Mise à jour des labels d'information
            self.ssid_label.config(text=f"SSID: {ssid}")
            self.auth_label.config(text=f"Authentification: {info.get('auth', 'N/A')}")
            self.encryption_label.config(text=f"Chiffrement: {info.get('encryption', 'N/A')}")
            
            # Mise à jour de la clé
            self.key_text.delete(1.0, tk.END)
            self.key_text.insert(tk.END, info.get('key', 'Clé non disponible'))

    def copy_key(self):
        key = self.key_text.get(1.0, tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(key)
        messagebox.showinfo("Succès", "Clé copiée dans le presse-papiers!")

    def __del__(self):
        # Nettoyage du répertoire temporaire
        try:
            os.rmdir(self.temp_dir)
        except:
            pass

def main():
    root = tk.Tk()
    app = WifiKeyViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
