
import sqlite3
import json
import os

OLD_DB = '/home/sandbox/calib.db'
NEW_DB = '/home/sandbox/Downloads/dll.db'

# Define table names
OLD_TABLE = 'calib_data'
NEW_TABLE = 'calib_table'

def map_column_name(old_name):
    """
    Converts old column format to new column format.
    """
    clean_name = old_name.strip('[]')
    clean_name = clean_name.replace('_', '__')
    clean_name = clean_name.replace('.', '_')
    return clean_name

def migrate_true_status():
    if not os.path.exists(OLD_DB) or not os.path.exists(NEW_DB):
        print("Error: Database files not found.")
        return

    conn_old = sqlite3.connect(OLD_DB)
    conn_old.row_factory = sqlite3.Row
    cursor_old = conn_old.cursor()

    conn_new = sqlite3.connect(NEW_DB)
    conn_new.row_factory = sqlite3.Row
    cursor_new = conn_new.cursor()

    try:
        print("Fetching the last record from the OLD database...")
        cursor_old.execute(f"SELECT * FROM {OLD_TABLE} ORDER BY id DESC LIMIT 1")
        old_row = cursor_old.fetchone()
        
        if not old_row:
            print("Old database is empty.")
            return

        print("Fetching the last record from the NEW database...")
        cursor_new.execute(f"SELECT * FROM {NEW_TABLE} ORDER BY id DESC LIMIT 1")
        template_row = cursor_new.fetchone()

        if not template_row:
            print("New database is empty.")
            return

        print(f"Duplicating ID {template_row['id']} into a new record...")
        
        columns = [col[0] for col in cursor_new.description if col[0] != 'id']
        
        values = [template_row[col] for col in columns]
        
        placeholders = ', '.join(['?'] * len(columns))
        columns_str = ', '.join(columns)
        
        cursor_new.execute(
            f"INSERT INTO {NEW_TABLE} ({columns_str}) VALUES ({placeholders})", 
            values
        )
        
        new_id = cursor_new.lastrowid
        conn_new.commit() # Save the copy immediately
        print(f"--- Created New Record ID {new_id} (Copy of {template_row['id']}) ---")
        
        cursor_new.execute(f"SELECT * FROM {NEW_TABLE} WHERE id = ?", (new_id,))
        target_row = cursor_new.fetchone()

        print(f"--- Applying Migration Updates to New ID {new_id} ---")

        new_valid_columns = [desc[0] for desc in cursor_new.description]

        updates = {} # Store changes

        for col_name in old_row.keys():
            if col_name in ['id', 'date', 'time', 'date_modified']:
                continue

            old_json_str = old_row[col_name]
            if not old_json_str: continue

            try:
                old_data = json.loads(old_json_str)
                
                path_content = old_data.get('path_content', {})
                if path_content.get('calib_status') is True:
                    
                    new_col_name = map_column_name(col_name)
                    
                    if new_col_name in new_valid_columns:
                        # Use the JSON from the NEW row (our copy)
                        new_json_str = target_row[new_col_name]
                        if new_json_str:
                            new_json_obj = json.loads(new_json_str)
                            
                            if 'data' not in new_json_obj:
                                new_json_obj['data'] = {}

                            # --- UPDATE LOGIC ---
                            if 'value' in path_content:
                                new_json_obj['data']['value'] = path_content['value']
                            
                            new_json_obj['data']['calib_status'] = True
                            
                            updates[new_col_name] = json.dumps(new_json_obj)
                            
            except json.JSONDecodeError:
                continue

        if updates:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            sql_values = list(updates.values())
            sql_values.append(new_id) 
            
            sql = f"UPDATE {NEW_TABLE} SET {set_clause} WHERE id = ?"
            cursor_new.execute(sql, sql_values)
            print(f" -> Success! Updated {len(updates)} columns in New ID {new_id}.")
        else:
            print(f" -> No active calibrations found to transfer.")

        conn_new.commit()
        print("------------------------------------------------")
        print(f"Migration Complete.")

    finally:
        conn_old.close()
        conn_new.close()

if __name__ == "__main__":
    migrate_true_status()