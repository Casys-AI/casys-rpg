from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import os
import logging

class NarratorAgent:
    """
    Agent narrateur qui lit et formate des sections de texte.
    """
    def __init__(self):
        self.logger = logging.getLogger('NarratorAgent')
        self.logger.info("Initialisation du NarratorAgent")
        
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.system_prompt = """Tu es un narrateur expert qui lit des sections de texte.
Ta mission est de présenter le texte de manière engageante tout en restant fidèle au contenu original.
Tu dois formater le texte pour qu'il soit agréable à lire, avec des paragraphes bien structurés.
Temperature: 0 - Tu ne dois pas modifier le sens ou ajouter du contenu."""
        self.cache_dir = os.path.join("data", "sections", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.logger.info(f"Dossier de cache créé: {self.cache_dir}")

    def read_section(self, section_path: str) -> str:
        """
        Lit et formate une section de texte. Retourne une chaîne vide si le fichier n'existe pas.
        """
        self.logger.debug(f"Lecture de la section: {section_path}")
        
        if not os.path.exists(section_path):
            self.logger.warning(f"Fichier non trouvé: {section_path}")
            return ""

        try:
            with open(section_path, 'r', encoding='utf-8') as f:
                text = f.read()
                self.logger.debug(f"Fichier lu avec succès ({len(text)} caractères)")

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Formate et présente ce texte de manière claire et engageante : {text}")
            ]

            self.logger.debug("Envoi au LLM pour formatage")
            response = self.llm.invoke(messages)
            self.logger.debug(f"Réponse reçue du LLM ({len(response.content)} caractères)")
            return response.content
            
        except Exception as e:
            self.logger.exception(f"Erreur lors de la lecture/formatage de la section: {str(e)}")
            return ""

    def get_section_content(self, section_number: int) -> str:
        """
        Récupère et formate le contenu d'une section.
        Utilise le cache si disponible, sinon traite et cache la section.
        """
        self.logger.info(f"Demande de contenu pour la section {section_number}")
        
        # Vérifier le cache
        cache_path = os.path.join(self.cache_dir, f"section_{section_number}.md")
        if os.path.exists(cache_path):
            self.logger.debug(f"Section {section_number} trouvée dans le cache")
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()  # Retourner directement le contenu du cache sans reformatage
        
        # Lire et traiter la section originale
        self.logger.debug(f"Section {section_number} non trouvée dans le cache, lecture du fichier original")
        raw_section_path = os.path.join("data", "sections", f"{section_number}.md")
        processed_content = self.read_section(raw_section_path)
        
        # Sauvegarder dans le cache
        if processed_content:
            self.logger.debug(f"Sauvegarde de la section {section_number} dans le cache")
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
        else:
            self.logger.warning(f"Pas de contenu à mettre en cache pour la section {section_number}")
        
        return str(processed_content)

    def format_text(self, text: str) -> str:
        """
        Formate un texte brut pour l'affichage.
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Formate ce texte pour l'affichage : {text}")
        ]
        self.logger.debug("Envoi au LLM pour formatage")
        response = self.llm.invoke(messages)
        self.logger.debug(f"Réponse reçue du LLM ({len(response.content)} caractères)")
        return response.content
