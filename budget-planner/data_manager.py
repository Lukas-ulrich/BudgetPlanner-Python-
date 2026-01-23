# ============================================
# data_manager.py - Datenverwaltung
# ============================================
import json
import os
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Transaction:
    """Einzelne Transaktion"""
    def __init__(self, amount: float = 0.0, note: str = ""):
        self.amount = amount
        self.note = note
    
    def to_dict(self) -> dict:
        return {"amount": self.amount, "note": self.note}
    
    @staticmethod
    def from_dict(data: dict) -> 'Transaction':
        return Transaction(
            amount=float(data.get("amount", 0.0)),
            note=str(data.get("note", ""))
        )


class MonthData:
    """Daten für einen Monat"""
    def __init__(self, month: str):
        self.month = month
        self.transactions: Dict[Tuple[str, str, str], Transaction] = {}
    
    def set_transaction(self, category: str, subcategory: str, item: str, transaction: Transaction):
        self.transactions[(category, subcategory, item)] = transaction
    
    def get_transaction(self, category: str, subcategory: str, item: str) -> Transaction:
        return self.transactions.get((category, subcategory, item), Transaction())
    
    def get_all_transactions(self) -> Dict[Tuple[str, str, str], Transaction]:
        return self.transactions.copy()


class DataManager:
    """Zentrale Datenverwaltung"""
    
    DEFAULT_STRUCTURE = {
        "Einnahmen": {
            "Gehalt": ["Gehalt Hauptjob", "Nebentätigkeit"],
            "Sonstiges": ["Geschenke", "Verkauf"]
        },
        "Fixkosten": {
            "Wohnen": ["Miete", "Strom", "Wasser"],
            "Versicherungen": ["Krankenversicherung", "Hausrat"]
        },
        "Variable Kosten": {
            "Essen": ["Supermarkt", "Restaurant"],
            "Freizeit": ["Abos", "Urlaub", "Kino"]
        },
        "Sparen": {
            "Ziele": ["Notgroschen", "Urlaub", "Rente"]
        }
    }
    
    def __init__(self, base_folder: str = "profiles", profile: str = "default"):
        self.base_folder = base_folder
        self.profile = profile
        self.structure = self.DEFAULT_STRUCTURE.copy()
        self.settings = {}
        self._ensure_directories()
        self.load_settings()
    
    def _ensure_directories(self):
        """Erstellt notwendige Verzeichnisse"""
        profile_path = os.path.join(self.base_folder, self.profile)
        os.makedirs(profile_path, exist_ok=True)
    
    def get_month_filename(self, month: str) -> str:
        """Gibt Dateipfad für einen Monat zurück"""
        return os.path.join(self.base_folder, self.profile, f"budget_{month}.json")
    
    def load_month(self, month: str) -> Optional[MonthData]:
        """Lädt Monatsdaten"""
        filename = self.get_month_filename(month)
        
        if not os.path.exists(filename):
            logger.info(f"Keine Daten für {month} gefunden")
            return None
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update structure if present
            if "structure" in data:
                self.structure = data["structure"]
            
            # Load transactions
            month_data = MonthData(month)
            values = data.get("values", {})
            
            for category, subcats in values.items():
                for subcat, items in subcats.items():
                    for item, trans_data in items.items():
                        transaction = Transaction.from_dict(trans_data)
                        month_data.set_transaction(category, subcat, item, transaction)
            
            logger.info(f"Monat {month} erfolgreich geladen")
            return month_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Fehler beim Laden von {month}: {e}")
            raise ValueError(f"Fehlerhafte JSON-Datei: {filename}")
        except Exception as e:
            logger.error(f"Fehler beim Laden von {month}: {e}")
            raise
    
    def save_month(self, month_data: MonthData) -> bool:
        """Speichert Monatsdaten"""
        filename = self.get_month_filename(month_data.month)
        
        try:
            # Build payload
            payload = {
                "structure": self.structure,
                "values": {}
            }
            
            for (category, subcat, item), transaction in month_data.get_all_transactions().items():
                if category not in payload["values"]:
                    payload["values"][category] = {}
                if subcat not in payload["values"][category]:
                    payload["values"][category][subcat] = {}
                payload["values"][category][subcat][item] = transaction.to_dict()
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Monat {month_data.month} erfolgreich gespeichert")
            return True
            
        except IOError as e:
            logger.error(f"IO-Fehler beim Speichern von {month_data.month}: {e}")
            raise
        except Exception as e:
            logger.error(f"Fehler beim Speichern von {month_data.month}: {e}")
            raise
    
    def load_settings(self):
        """Lädt App-Einstellungen"""
        settings_path = os.path.join(self.base_folder, "settings.json")
        
        if not os.path.exists(settings_path):
            self.settings = {
                'dark_mode': True,
                'auto_fill': True,
                'budget_warnings': {},
                'structure': self.DEFAULT_STRUCTURE.copy()
            }
            return
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
                if 'structure' in self.settings:
                    self.structure = self.settings['structure']
            logger.info("Einstellungen geladen")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            self.settings = {}
    
    def save_settings(self):
        """Speichert App-Einstellungen"""
        settings_path = os.path.join(self.base_folder, "settings.json")
        self.settings['structure'] = self.structure
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logger.info("Einstellungen gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            raise
    
    def add_category(self, main_category: str, subcategory: str = None, item: str = None):
        """Fügt Kategorie/Unterkategorie/Item hinzu"""
        if main_category not in self.structure:
            self.structure[main_category] = {}
        
        if subcategory and subcategory not in self.structure[main_category]:
            self.structure[main_category][subcategory] = []
        
        if subcategory and item and item not in self.structure[main_category][subcategory]:
            self.structure[main_category][subcategory].append(item)
            logger.info(f"Item '{item}' zu '{main_category}/{subcategory}' hinzugefügt")
        
        self.save_settings()
    
    def remove_item(self, main_category: str, subcategory: str, item: str):
        """Entfernt ein Item"""
        try:
            if item in self.structure[main_category][subcategory]:
                self.structure[main_category][subcategory].remove(item)
                logger.info(f"Item '{item}' entfernt")
            
            # Cleanup empty structures
            if not self.structure[main_category][subcategory]:
                del self.structure[main_category][subcategory]
            
            if not self.structure[main_category]:
                del self.structure[main_category]
            
            self.save_settings()
        except KeyError as e:
            logger.error(f"Item nicht gefunden: {e}")
    
    def export_csv(self, month_data: MonthData, filename: str):
        """Exportiert Monatsdaten als CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Hauptkategorie", "Unterkategorie", "Posten", "Betrag", "Notiz"])
                
                for (cat, subcat, item), trans in month_data.get_all_transactions().items():
                    writer.writerow([
                        cat,
                        subcat,
                        item,
                        str(trans.amount).replace('.', ','),
                        trans.note
                    ])
            
            logger.info(f"CSV exportiert: {filename}")
            return True
        except Exception as e:
            logger.error(f"CSV-Export fehlgeschlagen: {e}")
            raise
    
    def import_bank_csv(self, filename: str, amount_col: str, desc_col: str, 
                       category_mapping: Dict[str, Tuple[str, str, str]] = None) -> List[Transaction]:
        """
        Importiert Bank-CSV mit intelligenter Kategoriezuordnung
        
        Args:
            filename: CSV-Datei
            amount_col: Spaltenname für Betrag
            desc_col: Spaltenname für Beschreibung
            category_mapping: Dict[keyword] -> (category, subcategory, item)
        
        Returns:
            Liste erkannter Transaktionen
        """
        if category_mapping is None:
            category_mapping = self._get_default_category_mapping()
        
        transactions = []
        
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                for row in reader:
                    try:
                        # Parse amount
                        amount_str = row[amount_col].replace('.', '').replace(',', '.')
                        amount = float(amount_str)
                        
                        # Get description
                        description = row[desc_col].lower()
                        
                        # Match category
                        matched_category = None
                        for keyword, (cat, subcat, item) in category_mapping.items():
                            if keyword.lower() in description:
                                matched_category = (cat, subcat, item)
                                break
                        
                        transaction = Transaction(amount, row[desc_col])
                        if matched_category:
                            transaction.category = matched_category
                        
                        transactions.append(transaction)
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Zeile übersprungen: {e}")
                        continue
            
            logger.info(f"{len(transactions)} Transaktionen importiert")
            return transactions
            
        except Exception as e:
            logger.error(f"CSV-Import fehlgeschlagen: {e}")
            raise
    
    def _get_default_category_mapping(self) -> Dict[str, Tuple[str, str, str]]:
        """Standard-Mapping für CSV-Import"""
        return {
            "rewe": ("Variable Kosten", "Essen", "Supermarkt"),
            "edeka": ("Variable Kosten", "Essen", "Supermarkt"),
            "aldi": ("Variable Kosten", "Essen", "Supermarkt"),
            "lidl": ("Variable Kosten", "Essen", "Supermarkt"),
            "restaurant": ("Variable Kosten", "Essen", "Restaurant"),
            "netflix": ("Variable Kosten", "Freizeit", "Abos"),
            "spotify": ("Variable Kosten", "Freizeit", "Abos"),
            "miete": ("Fixkosten", "Wohnen", "Miete"),
            "strom": ("Fixkosten", "Wohnen", "Strom"),
            "gehalt": ("Einnahmen", "Gehalt", "Gehalt Hauptjob"),
        }
