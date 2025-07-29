from .storage import *
from fastapi import FastAPI, Depends, Body, BackgroundTasks
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi.responses import JSONResponse
import asyncio
import threading
from contextlib import asynccontextmanager
import queue
import requests
import ansible_runner
from pathlib import Path
import uuid

APP_DIR = Path(__file__).parent.resolve()

DB_QUERY_INTERVAL_SECONDS = 60 * 30
DB_REQUEST_AGE_SECONDS = 60 * 10

INFOAPI_URL = "https://spb99-it-scor01/v1/infoinstall"
#INFOAPI_URL = "https://appstore.free.beeceptor.com/infoinstall"

#test_inventory=APP_DIR / 'ansible-runner/inventory.ini'

Base.metadata.create_all(bind=engine)

task_queue = queue.Queue()

def my_event_handler(event_data):
    result = event_data.get('event_data', {}).get('res', {})
    msg = result.get('msg')
    if msg:
        print("install response:")
        print(msg)

# get unprocessed tasks from db (use timestamps and status)
async def db_worker_async():
    while True:
        print("polling requests from db")
        now = datetime.now()
        time_difference = now - timedelta(seconds = DB_REQUEST_AGE_SECONDS)
        with SessionLocal() as db:
            requests = db.query(Request).filter((Request.status == "pending" 
                                                or Request.status == "installing")
                                                and Request.modified_at < time_difference).limit(100).all()
            print(requests)
            db.close()
            for request in requests:
                task_queue.put(request)
        await asyncio.sleep(DB_QUERY_INTERVAL_SECONDS)
        
def worker():
    while True:
        request_data = task_queue.get()
        request_data.status = "installing"
        print("from queue", request_data)
        
        with SessionLocal() as db:
            request_record = db.query(Request).filter(Request.id == request_data.id).first()
            request_record.status = "installing"
            print("updating db installing")
            db.commit()    
            db.close()
            
        #time.sleep(20)
        # run ansible playbook on host
        curr_inventory = request_data.hostname+","
        #curr_inventory = test_inventory
        playbook_name = "install_pkg.yml"
        if request_data.package.endswith(".yml"):
            playbook_name = request_data.package
        r = ansible_runner.run(private_data_dir=APP_DIR / 'ansible-runner', 
                               playbook=playbook_name, 
                               inventory=curr_inventory,
                               extravars={"package_name":request_data.package}
                               )
        # get response
        print("processing done", request_data)
        install_status = "failed"
        
        result_dict = None
        for event in r.events:
            # print(event)
            if event.get('event') == 'playbook_on_stats':
                result_dict = event['event_data']['artifact_data'].get('install_status')
                break
        #print(result_dict)
        #print(request_data.id)
        
        # result_dict for multiple install items is different
        # "{{ install_result.results if install_result.results is defined 
        # else [install_result] }}"
        
        if not result_dict["failed"]:
            if result_dict["changed"]:
                install_status = "installed"
            else:
                install_status = "skipped"
                    
        # update status in db
        with SessionLocal() as db:
            request_record = db.query(Request).filter(Request.id == request_data.id).first()
            request_record.status = install_status
            print("updating db installed")
            db.commit()    
            db.close()
            
        exitCode = 1
        if install_status == "installed":
            exitCode = 0
             
        # send response to Orchestrator
        install_response = {
            "RequestGuid": str(request_data.id),  # Convert UUID to string for JSON serialization
            "UserName": request_data.username,
            "ApplicationName":request_data.package,
            "ComputerName":request_data.hostname,
            "ComputerIP":request_data.ip,
            "Action":True,
            "ExitCode":exitCode,
            "System":"AstraLinux"
        }
        
        response = requests.post(INFOAPI_URL,json=install_response)    
        print(response.status_code)
        print(response.json())
        
        task_queue.task_done()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
#status - pending -> installing -> installed/failed




async def process_request(request):
    print("process_request", request)
    return "result"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup:")
    t1 = threading.Thread(target=worker, daemon=True)
    t1.start()
    loop = asyncio.get_event_loop()
    loop.create_task(db_worker_async())
    # Shutdown: Unload or clean up the model
    yield
    print("Application shutdown:")
    

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return "hi"

@app.get("/api/v1/requests")
async def get_requests(db: Session = Depends(get_db)):
    return db.query(Request).order_by(desc(Request.created_at)).limit(100).all()

@app.get("/api/v1/requests/pending")
async def get_pending_requests(db: Session = Depends(get_db)):
    print("pending")
    requests = db.query(Request).filter(Request.status == "pending").all()
    if requests is None:
        return JSONResponse(status_code=404, content={"message":"Requests not found"})
    return requests

@app.get("/api/v1/requests/{id}")
async def get_request(id: str, db: Session = Depends(get_db)):  # Accept id as string
    print("id")
    try:
        # Convert string to UUID for PostgreSQL query
        uuid_id = uuid.UUID(id)
        request = db.query(Request).filter(Request.id == uuid_id).first()
        if request is None:
            return JSONResponse(status_code=404, content={"message":"Request not found"})
        return request
    except ValueError:
        return JSONResponse(status_code=400, content={"message":"Invalid UUID format"})

@app.post("/api/v1/requests")
async def create_request(data = Body(), db: Session = Depends(get_db)):
    print(data)
    # Handle UUID conversion
    request_id = data["request_id"]
    if isinstance(request_id, str):
        try:
            request_id = uuid.UUID(request_id)
        except ValueError:
            return JSONResponse(status_code=400, content={"message":"Invalid UUID format"})
    
    request = Request(id=request_id,
                      package=data["install_pkg"],
                      status = "pending",
                      username=data["username"],
                      ip=data["ip"],
                      hostname=data["hostname"])
    db.add(request)
    db.commit()
    db.refresh(request)
    task_queue.put(request)
    return request

@app.put("/api/v1/requests/{id}/{status}")
async def update_request_status(id: str, status: str, db: Session = Depends(get_db)):
    print(id, status)
    try:
        # Convert string to UUID for PostgreSQL query
        uuid_id = uuid.UUID(id)
        request = db.query(Request).filter(Request.id == uuid_id).first()
        if request is None:
            return JSONResponse(status_code=404, content={"message":"Request not found"})
        request.status = status
        db.commit()
        db.refresh(request)
        return request
    except ValueError:
        return JSONResponse(status_code=400, content={"message":"Invalid UUID format"})