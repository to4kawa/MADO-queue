#!/usr/bin/env python3
"""SQLite-only verification for upstream PR #3 concurrency behavior."""
import json, multiprocessing as mp, os, sqlite3, tempfile, threading, time
from datetime import datetime
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE numbers (category CHAR(1) PRIMARY KEY,current_number INTEGER NOT NULL,timestamp DATE);
CREATE TABLE event_logs (id INTEGER PRIMARY KEY AUTOINCREMENT,category CHAR(1) NOT NULL,button_text TEXT,timestamp TEXT NOT NULL,current_number INTEGER NOT NULL,staff_count INTEGER);
CREATE TABLE processing_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_log_id INTEGER NOT NULL REFERENCES event_logs(id),
 ticket_number INTEGER NOT NULL,category CHAR(1),button_text TEXT,start_time TEXT,end_time TEXT,wait_time INTEGER,
 status TEXT NOT NULL CHECK (status IN ('processing','completed','deleted')),
 processing_time INTEGER,created_at TEXT NOT NULL,staff_count INTEGER);
CREATE INDEX idx_pl_event_log_id ON processing_logs(event_log_id);
CREATE INDEX idx_pl_status ON processing_logs(status);
"""

def connect(path, timeout=0.2):
    c=sqlite3.connect(path, timeout=timeout, isolation_level=None)
    c.execute('PRAGMA foreign_keys=ON')
    return c

def setup_db(path):
    c=connect(path); c.executescript(SCHEMA)
    now=datetime.now().isoformat()
    c.execute("INSERT INTO event_logs(category,button_text,timestamp,current_number,staff_count) VALUES('A','test',?,1,2)",(now,))
    c.close(); return 1

def start_like_pr3(path, event_log_id, name, barrier=None, delay_after_select=0.05):
    out={'name':name,'select_result':None,'insert':'not_attempted','database_is_locked':False,'error':None}
    try:
        con=connect(path)
        cur=con.cursor()
        if barrier: barrier.wait()
        ev=cur.execute('SELECT current_number, category, button_text, timestamp, staff_count FROM event_logs WHERE id = ?', (event_log_id,)).fetchone()
        out['event_row']=ev
        sel=cur.execute("SELECT 1 FROM processing_logs WHERE event_log_id = ? AND status = 'processing'", (event_log_id,)).fetchone()
        out['select_result']=sel
        if sel:
            out['insert']='skipped_already_processing'; con.close(); return out
        time.sleep(delay_after_select)
        now=datetime.now().isoformat(); ticket_number, category, button_text, issued_ts, staff_count=ev
        try:
            cur.execute("INSERT INTO processing_logs (event_log_id,ticket_number,category,button_text,start_time,wait_time,status,created_at,staff_count) VALUES (?,?,?,?,?,?,'processing',?,?)", (event_log_id,ticket_number,category,button_text,now,0,now,staff_count))
            con.commit(); out['insert']='success'
        except sqlite3.OperationalError as e:
            out['insert']='failed'; out['error']=str(e); out['database_is_locked']='database is locked' in str(e)
        finally: con.close()
    except Exception as e:
        out['error']=repr(e); out['database_is_locked']='database is locked' in str(e)
    return out

def final_state(path):
    con=connect(path)
    total=con.execute('SELECT COUNT(*) FROM processing_logs').fetchone()[0]
    active=con.execute("SELECT event_log_id, COUNT(*) FROM processing_logs WHERE status='processing' GROUP BY event_log_id HAVING COUNT(*)>1").fetchall()
    rows=con.execute('SELECT id,event_log_id,status FROM processing_logs ORDER BY id').fetchall()
    con.close(); return {'total_processing_logs':total,'duplicate_active_processing':active,'rows':rows}

def case_sequential(tmp):
    path=str(tmp/'seq.db'); setup_db(path)
    r1=start_like_pr3(path,1,'seq-1',None,0); r2=start_like_pr3(path,1,'seq-2',None,0)
    return {'attempts':[r1,r2], 'final':final_state(path)}

def case_threads(tmp):
    path=str(tmp/'threads.db'); setup_db(path); b=threading.Barrier(2); res=[]
    ts=[threading.Thread(target=lambda n=n: res.append(start_like_pr3(path,1,n,b,0.1))) for n in ('thread-1','thread-2')]
    [t.start() for t in ts]; [t.join() for t in ts]
    return {'attempts':sorted(res,key=lambda x:x['name']), 'final':final_state(path)}

def proc_worker(path, name, barrier, q): q.put(start_like_pr3(path,1,name,barrier,0.1))

def case_processes(tmp):
    path=str(tmp/'procs.db'); setup_db(path); b=mp.Barrier(2); q=mp.Queue()
    ps=[mp.Process(target=proc_worker,args=(path,n,b,q)) for n in ('proc-1','proc-2')]
    [p.start() for p in ps]; [p.join() for p in ps]
    res=[q.get() for _ in ps]
    return {'attempts':sorted(res,key=lambda x:x['name']), 'final':final_state(path)}

def schema_checks(tmp):
    path=str(tmp/'schema.db'); setup_db(path); con=connect(path)
    indexes=con.execute("PRAGMA index_list(processing_logs)").fetchall()
    index_details={i[1]:con.execute(f"PRAGMA index_info({i[1]})").fetchall() for i in indexes}
    create_sql=con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='processing_logs'").fetchone()[0]
    has_unique=any(i[2] for i in indexes) or 'UNIQUE' in create_sql.upper()
    con.close(); return {'indexes':indexes,'index_details':index_details,'create_sql':create_sql,'has_unique_or_partial_unique':has_unique}

def update_delete_checks(tmp):
    path=str(tmp/'upd_del.db'); setup_db(path); con=connect(path); now=datetime.now().isoformat()
    for e in (1,1): con.execute("INSERT INTO processing_logs(event_log_id,ticket_number,category,button_text,start_time,wait_time,status,created_at,staff_count) VALUES(?,1,'A','test',?,0,'processing',?,2)",(e,now,now))
    con.commit(); target=1
    con.execute("UPDATE processing_logs SET end_time=?, processing_time=?, status='completed' WHERE id=? AND status='processing'",(now,1,target)); upd=con.execute('SELECT changes()').fetchone()[0]
    con.execute("DELETE FROM processing_logs WHERE id=? AND status='processing'",(2,)); dele=con.execute('SELECT changes()').fetchone()[0]
    rows=con.execute('SELECT id,status FROM processing_logs ORDER BY id').fetchall(); con.close()
    return {'update_changes':upd,'delete_changes':dele,'remaining_rows':rows}

def migrate_once(path):
    con=connect(path); before=con.execute('PRAGMA foreign_key_check').fetchall(); after=[]; msg=[]
    # If FK to event_logs already exists, PR #3 safe_migrate_db.py is a no-op.
    fks=con.execute('PRAGMA foreign_key_list(processing_logs)').fetchall()
    if any(fk[2]=='event_logs' for fk in fks): msg.append('Already migrated (FK to event_logs present). Nothing to do.')
    after=con.execute('PRAGMA foreign_key_check').fetchall(); con.close(); return {'messages':msg,'fk_before':before,'fk_after':after}

def migration_checks(tmp):
    path=str(tmp/'migrate.db'); setup_db(path)
    return {'run1':migrate_once(path),'run2':migrate_once(path)}

def main():
    with tempfile.TemporaryDirectory(prefix='pr3-sqlite-') as d:
        tmp=Path(d)
        results={'sequential':case_sequential(tmp),'threads':case_threads(tmp),'processes':case_processes(tmp),'schema':schema_checks(tmp),'update_delete':update_delete_checks(tmp),'migration':migration_checks(tmp)}
    print(json.dumps(results,ensure_ascii=False,indent=2,default=str))
if __name__=='__main__': main()
