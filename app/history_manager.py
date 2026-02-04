import json
import datetime
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def save_history(entry):
    try:
        if supabase:
            # Insert into Supabase table 'history'
            supabase.table('history').insert(entry).execute()
        else:
            # Fallback to file
            HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history.json")
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                history = []
            
            history.append(entry)
            
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving history: {e}")
        # Continue without raising

def get_history():
    try:
        if supabase:
            response = supabase.table('history').select('*').order('timestamp', desc=True).execute()
            return response.data
        else:
            # Fallback to file
            HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history.json")
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return []
    except Exception as e:
        print(f"Error getting history: {e}")
        return []